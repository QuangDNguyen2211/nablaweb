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
        for (alt_pk, pri) in zip(alt_pks, ballot):
            alternative = self.alternatives.get(pk=alt_pk)
            priority_count = alternative.priority_dict.entries.get(priority=pri)
            priority_count.raise_count(user)
            self.users_voted.add(user)

    def get_multi_winner_result(self):
        # STV
        alternatives = self.alternatives.all()
        priorities = range(1, alternatives.count()+1)
            

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


class PriorityDict(models.Model):
    """ 
    Dictonary like model storing priority and # times the given alternative received that priority

    E.g. for

    Person A:
        {1: 5, 2:3, 3:5}

    Five people have given Person A priority 1, 3 people priority 2, and five people priority 3
    """
    alternative = models.OneToOneField(
            Alternative, on_delete=models.CASCADE, related_name="priority_dict")


class PriorityCount(models.Model):
    """ priority and # 'votes' as key:value """
    dictionary = models.ForeignKey(PriorityDict, on_delete=models.CASCADE, related_name="entries")
    priority = models.IntegerField()
    count = models.IntegerField()

    def raise_count(self, user):
        self.count += 1
        self.save()
