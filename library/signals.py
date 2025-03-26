from datetime import timedelta

from django.db.models. signals import post_save
from django.dispatch import receiver

from .models import Loan

@receiver(post_save, sender=Loan)
def set_default_due_date(sender, instance, created, ** kwargs) :
    if created:
        instance.due_date = instance.loan_date + timedelta(days=14)
        instance.save()
        print("loan due date updated.")
