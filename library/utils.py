from django.core.mail import send_mail
from django.conf import settings

def send_email_reminder(loan):
    member_email = loan.member.user.email
    book_title = loan.book.title
    send_mail(
        subject='Loan Overdue Reminder',
        message=f'Hello {loan.member.user.username},\n\nYour loan is overdue for book "{book_title}".',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[member_email],
        fail_silently=False,
    )
