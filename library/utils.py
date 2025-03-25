

def send_email_reminder(loan):
    member_email = loan.member.user.email
    book_title = loan.book.title
    send_mail(
        subject='Book Reminder',
        message=f'Hello {loan.member.user.username},\n\nYour due date is passed for book "{book_title}"',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[member_email],
        fail_silently=False,
    )