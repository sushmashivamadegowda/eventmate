from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Event, Booking, Review


class EventSearchForm(forms.Form):
    """Search and filter form"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search events...',
            'class': 'form-control'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Location',
            'class': 'form-control'
        })
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + Event.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Min Price',
            'class': 'form-control'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Max Price',
            'class': 'form-control'
        })
    )
    sort = forms.ChoiceField(
        required=False,
        choices=[
            ('-created_at', 'Newest'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
            ('start_date', 'Date'),
            ('popular', 'Most Popular'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class EventForm(forms.ModelForm):
    """Form for creating/editing events"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'city', 'location',
            'start_date', 'end_date', 'start_time', 'price', 'capacity',
            'included', 'things_to_know', 'cancellation_policy', 'age_restriction'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your event...'
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Venue name or address'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'included': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': "What's included in the ticket price?"
            }),
            'things_to_know': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Important information for attendees'
            }),
            'cancellation_policy': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'age_restriction': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., All ages, 18+, 21+'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate dates
        if start_date and start_date < date.today():
            raise ValidationError('Start date cannot be in the past.')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError('End date must be after start date.')
        
        return cleaned_data


class BookingForm(forms.ModelForm):
    """Form for booking tickets"""
    
    class Meta:
        model = Booking
        fields = ['tickets', 'event_date']
        widgets = {
            'tickets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Number of tickets'
            }),
            'event_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
    
    def clean_tickets(self):
        tickets = self.cleaned_data.get('tickets')
        
        if tickets < 1:
            raise ValidationError('Must book at least 1 ticket.')
        
        if self.event and tickets > self.event.available_tickets:
            raise ValidationError(
                f'Only {self.event.available_tickets} tickets available.'
            )
        
        return tickets
    
    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        
        if event_date < date.today():
            raise ValidationError('Cannot book for past dates.')
        
        if self.event:
            if event_date < self.event.start_date or event_date > self.event.end_date:
                raise ValidationError(
                    f'Event runs from {self.event.start_date} to {self.event.end_date}.'
                )
        
        return event_date


class ReviewForm(forms.ModelForm):
    """Form for adding reviews"""
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[
                (5, '5 ★★★★★'),
                (4, '4 ★★★★'),
                (3, '3 ★★★'),
                (2, '2 ★★'),
                (1, '1 ★'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share your experience...'
            }),
        }
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise ValidationError('Rating must be between 1 and 5.')
        return rating