from datetime import timedelta
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Count, F
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer, MemberTopActiveSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_queryset(self):
        return self.queryset.select_related('author')

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    action_serializer = {
        'top_active': MemberTopActiveSerializer
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializer'):
            return self.action_serializer.get(self.action, self.serializer_class)

        return super(MemberViewSet, self).get_serializer_class()

    @action(detail=False, methods=['get'], url_path='top-active')
    def top_active(self, request):

        top_active_members = self.queryset.select_related('user').annotate(
            active_loans= Count('loans'),
            email=F('user__email'),
            username=F('user__username')
        ).order_by('-active_loans')[:5].values(
            'id',
            'username',
            'email',
            'active_loans',
        )
        
        return Response(
            self.get_serializer(
                top_active_members,
                many=True,
            ).data,
            status=status.HTTP_200_OK
        )

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=['post'])
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()
        additional_days = request.data.get('additional_days', None)

        if not additional_days:
            return Response({'error': 'additional_days parameter is missing.'}, status=status.HTTP_400_BAD_REQUEST)

        if additional_days < 0:
            return Response({'error': 'additional_days must be a positive number.'}, status=status.HTTP_400_BAD_REQUEST)

        if loan.due_date < timezone.now().date():
            return Response({'error': 'Loan is already overdue.'}, status=status.HTTP_400_BAD_REQUEST)

        loan.due_date = loan.due_date + timedelta(days=additional_days)
        loan.save()

        return Response(self.get_serializer(loan).data, status=status.HTTP_200_OK)
