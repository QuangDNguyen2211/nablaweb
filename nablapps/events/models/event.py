"""
The Event model
"""
import logging
from django.urls import reverse
from django.db import IntegrityError, models
from django.core.exceptions import ValidationError

from ..exceptions import RegistrationAlreadyExists, EventFullException, DeregistrationClosed
from .eventregistration import EventRegistration

from nablapps.core.models import (
    TimeStamped,
    WithPicture,
)
from nablapps.news.models import TextContent
from .mixins import RegistrationInfoMixin, EventInfoMixin
from nablapps.jobs.models import Company


class Event(RegistrationInfoMixin, EventInfoMixin,
            TimeStamped, TextContent, WithPicture):
    """Arrangementer både med og uten påmelding.
    Dukker opp som nyheter på forsiden.
    """

    is_bedpres = models.BooleanField(default=False)

    # Company is required if is_bedpres is True, see clean()
    company = models.ForeignKey(
        Company,
        verbose_name="Bedrift",
        blank=True,
        null=True, 
        on_delete=models.CASCADE,
        help_text="Kun relevant for bedriftspresentasjoner.")

    def clean(self):
        if self.is_bedpres and self.company is None:
            raise ValidationError("Company must be set when 'is_bedpres' is True!")
        if not self.is_bedpres and self.company is not None:
            raise ValidationError("Company should only be set for bedpres!")

    class Meta:
        verbose_name = "arrangement"
        verbose_name_plural = "arrangement"
        permissions = (
            ("administer", "Can administer models"),
        )
        db_table = "content_event" # Todo: hvorfor ha det slik?

    def __str__(self):
        return '%s, %s' % (self.headline, self.event_start.strftime('%d.%m.%y'))

    def get_short_name(self):
        """Henter short_name hvis den finnes, og kutter av enden av headline hvis ikke."""
        return self.short_name if self.short_name else (self.headline[0:18].capitalize() + '...')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.move_waiting_to_attending()

    @property
    def waiting_registrations(self):
        return self.eventregistration_set.filter(attending=False)

    @property
    def attending_registrations(self):
        return self.eventregistration_set.filter(attending=True)

    def free_places(self):
        """Returnerer antall ledige plasser.

        dvs antall plasser som umiddelbart gir brukeren en garantert plass, og ikke bare
        ventelisteplass.
        Returnerer 0 hvis self.places er None.
        """
        try:
            return max(self.places - self.users_attending(), 0)
        except TypeError:
            return 0

    def is_full(self):
        """Return whether all places in the event are occupied"""
        return self.free_places() == 0

    def users_attending(self):
        """Returnerer antall brukere som er påmeldt."""
        return self.attending_registrations.count()

    def users_attending_emails(self):
        """
        :return: List of attending users emails.
        """
        attending = self.attending_registrations
        return [att.user.email for att in attending]

    def users_waiting(self):
        """Returnerer antall brukere som står på venteliste."""
        return self.waiting_registrations.count()

    def percent_full(self):
        """Returnerer hvor mange prosent av plassene som er tatt."""
        try:
            return min(self.users_attending() * 100 / int(self.places), 100)
        except TypeError:
            return 0
        except ZeroDivisionError:
            return 100

    def is_registered(self, user):
        return self.eventregistration_set.filter(user=user).exists()

    def is_attending(self, user):
        return self.attending_registrations.filter(user=user).exists()

    def is_waiting(self, user):
        return self.waiting_registrations.filter(user=user).exists()

    def get_attendance_list(self):
        return [e.user for e in self.attending_registrations]

    def get_waiting_list(self):
        return [e.user for e in self.waiting_registrations]

    def register_user(self, user, ignore_restrictions=False):
        """
        Tries to register a user for an event.

        If the user is not allowed to attend, an exception will be thrown.
        Set ignore_restrictions to True to register a user anyways.
        """
        if not ignore_restrictions:
            self._assert_user_allowed_to_register(user)

        registration = EventRegistration(
            event=self,
            user=user,
        )
        if not self.is_full() or ignore_restrictions:
            registration.attending = True
        elif self.has_queue:
            registration.attending = False
        else:
            raise EventFullException(event=self, user=user)
        try:
            registration.save()
        except IntegrityError:
            raise RegistrationAlreadyExists(event=self, user=user)
        return registration

    def deregister_user(self, user, respect_closed=True):
        """
        Melder brukeren av arrangementet.
        respect_closed gir mulighet til å avmelde brukere etter avmeldingsfrist,
        fra administrative verktøy
        """
        regs = self.eventregistration_set
        if self.deregistration_closed() and respect_closed:
            raise DeregistrationClosed(event=self, user=user)
        try:
            reg = regs.get(user=user)
            reg.delete()
        except EventRegistration.DoesNotExist:
            logger = logging.getLogger(__name__)
            logger.info('Attempt to deregister user from non-existent event.')

    def move_waiting_to_attending(self):
        """
        Moves as many as there are free places left on the event.
        """
        free_places = self.free_places()
        waiting_regs = self.waiting_registrations[:free_places]
        for reg in waiting_regs:
            reg.set_attending_and_send_email()

    def get_registration_url(self):
        return reverse('registration', kwargs={'pk': self.pk})

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={'pk': self.pk, 'slug': self.slug})

def attending_events(user, today):
    """Get the future events attended by a user"""
    if user.is_anonymous:
        return []
    regs = user.eventregistration_set.filter(event__event_start__gte=today)
    events = []
    for reg in regs:
        event = reg.event
        event.attending = reg.attending
        event.waiting = not reg.attending
        events.append(event)
    return events
