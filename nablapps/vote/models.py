from django.conf import settings
from django.db import models

from nablapps.accounts.models import NablaGroup

"""
These models are esentially the same as in poll/models.
Code heavily boiled.
"""


class VotingEvent(models.Model):
    title = models.CharField(max_length=100)
    creation_date = models.DateTimeField("Opprettet", auto_now_add=True)
    checked_in_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="checked_in_users"
    )
    eligible_group = models.ForeignKey(
        NablaGroup,
        on_delete=models.CASCADE,
        related_name="voting_events",
        blank=True,
        null=True,
    )

    class Meta:
        permissions = [
            ("vote_admin", "can administer voting"),
            ("vote_inspector", "can inspect voting"),
        ]

    def __str__(self):
        return self.title


class UserAlreadyVoted(Exception):
    """Raised if the voting user has already voted on a voting"""


class UserNotEligible(Exception):
    """Raised if the voting user is not eligible to vote"""


class VotingDeactive(Exception):
    """Raised if the user tries to vote on an inactive voting"""


class DuplicatePriorities(Exception):
    """Raised if users tries to submit a STV ballot with dubplicate canditate(s) accross priorities"""

class UnableToSelectWinners(Exception):
    """Raised if unable to select winners in multi winner election"""


class Voting(models.Model):
    """Represents a voting"""

    event = models.ForeignKey(
        VotingEvent, on_delete=models.CASCADE, related_name="votings"
    )
    title = models.CharField(max_length=100)
    num_winners = models.IntegerField(blank=False, default=1)
    description = models.TextField()
    users_voted = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="users_voted",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="Voting_created_by",
        verbose_name="Opprettet av",
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField("Åpen for avtemning?", default=False)

    def __str__(self):
        return self.title

    def user_already_voted(self, user):
        """returns true if the given user has already voted"""
        return user in self.users_voted.all()

    def get_total_votes(self):
        """Return the sum of votes for all belonging alternatives"""
        return self.users_voted.all().count()

    def get_num_alternatives(self):
        """ Returns the number of related/belinging alternatives"""
        return len(self.alternatives.all())

    def activate(self):
        """Activates voting and opens for voting"""
        self.is_active = True

    def deactivate(self):
        """Deactivates voting and closes for voting"""
        self.is_active = False

    def user_not_eligible(self, user):
        if self.event.eligible_group != None:
            if user.groups.all().filter(name=self.event.eligible_group).exists():
                return False
            else:
                return True
        else:
            return False

    def submit_stv_votes(self, user, ballot):
        """ Submits transferable votes """
        alt_pks = [int(ballot[pri]) for pri in ballot]
        if len(alt_pks) != len(set(alt_pks)):
            raise DuplicatePriorities(f"Ballot contains duplicate(s) of candidates")
        alt1_pk = int(ballot[1])
        alt1 = self.alternatives.get(pk=alt1_pk)
        new_ballot = BallotContainer.objects.create(voting=self, alternative=alt1)
        new_ballot.save()
        for (alt_pk, pri) in zip(alt_pks, ballot):
            alt = Alternative.objects.get(pk=alt_pk)
            new_entry = BallotEntry.objects.create(container=new_ballot, priority=pri, alternative=alt)
            new_entry.save()
            self.users_voted.add(user)

    def get_multi_winner_result(self):
        """Declare multples winners using a single transferable votes system"""
        alternatives = self.alternatives.all()
        quota = int(self.get_total_votes()/alternatives.count()+1) + 1 # Droop quota
        winners = []
        losers = []
        if self.get_total_votes() > quota:
            while len(winners) < self.num_winners:
                new_winners = {}
                # Find alternatives passing quota, add to winners
                for alt in alternatives:
                    if alt in winners:
                        break
                    if alt.ballots.all().count() >= quota:
                        num_surplus_votes = alt.ballots.all().count() - quota
                        new_winners[alt] = num_surplus_votes
                        winners.append[alt]
                # Sort winners and surpluses in order of descending surplus
                new_winners_sorted = sorted(new_winners.items(), key=lambda x:x[1], reverse=True)
                for winner, surplus in new_winners_sorted:
                    # For winners, distribute surplus votes of winners in order of descending surplus
                    # number of ballots equal to the surplus draw at random from winners ballots
                    # and redistributed
                    ballots = winner.ballots.all()
                    redist_indices = random.sample(range(ballots.count()), surplus)
                    for i in redist_indices:
                        # For each selected ballot, transfer it to next priority alternative
                        ballot = ballots[i]
                        pri = ballot.entries.get(alternative=winner).priority
                        next_prioritezed_alt = ballot.entries.get(priority=pri+1).alternative
                        ballot.alternative = next_prioritezed_alt
                if len(winners) < self.num_winners and self.get_total_votes() > quota:
                    # Find loser
                    loser = alternatives[0]
                    i = 1
                    while loser in losers:
                        loser = alternatives[i]
                        i+=1
                    for alt in alternatives[i:]:
                        if loser.ballots.all().count() > alt.ballots.all().count():
                            if not alt in losers:
                                loser = alt
                    losers.append(loser)
                    # Redistribute all losers votes
                    for ballot in loser.ballots.all():
                        pri = ballot.entries.get(alternative=loser).priority
                        next_prioritezed_alt = ballot.entries.get(priority=pri+1).alternative
                        ballot.alternative = next_prioritezed_alt
                if len(losers) + len(winners) >= alternatives.count() and len(winners) < self.num_winners:
                    break
        return winners


class Alternative(models.Model):
    """Represents an alternative"""

    voting = models.ForeignKey(
        Voting, on_delete=models.CASCADE, related_name="alternatives"
    )
    text = models.CharField(max_length=250)
    votes = models.IntegerField("Antall stemmer", blank=False, default=0)

    def __str__(self):
        return self.text

    def add_vote(self, user):
        """Add users vote"""
        if self.voting.user_already_voted(user):
            raise UserAlreadyVoted(f"{user} has already voted on {self.voting}.")
        elif self.voting.user_not_eligible(user):
            raise UserNotEligible(f"{user} is not eligible to vote on {self.voting}")
        elif not self.voting.is_active:
            raise VotingDeactive(f"This voting is no longer open for voting.")
        else:
            self.votes += 1
            self.save()
            self.voting.users_voted.add(user)

    def get_vote_percentage(self):
        """Return the percentage of the total votes this alternative got"""
        if self.voting.get_total_votes() == 0:
            return 0
        else:
            return 100 * self.votes / self.voting.get_total_votes()


class BallotContainer(models.Model):
    """ 
    Dictonary like model storing ballot with priority and alternative

    E.g. for

    Voter A:
        {1: alt2, 2:alt1, 3:alt3}

    has alt2 as first choice, alt1 as second choice and alt3 as third choice
    """
    voting = models.ForeignKey(Voting, on_delete=models.CASCADE, related_name="ballots")
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE, related_name="ballots")


class BallotEntry(models.Model):
    """ priority and # 'votes' as key:value """
    container = models.ForeignKey(BallotContainer, on_delete=models.CASCADE, related_name="entries")
    priority = models.IntegerField()
    alternative = models.ForeignKey(Alternative, on_delete=models.CASCADE)
