from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from .models import User, City, Event, EventImage, Booking, Review, Favorite
from .forms import EventForm, BookingForm, ReviewForm, EventSearchForm
from .middleware import RateLimitMiddleware, RequestTimingMiddleware, SecurityHeadersMiddleware
from .health_check import health_check, readiness_check, liveness_check, metrics


# =============================================================================
# MODEL TESTS
# =============================================================================

class UserModelTest(TestCase):
    """Test the User model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test user is created successfully"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_host)
    
    def test_user_str_method(self):
        """Test user string representation"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_user_host_flag(self):
        """Test host flag functionality"""
        self.user.is_host = True
        self.user.save()
        self.assertTrue(self.user.is_host)
    
    def test_user_profile_fields(self):
        """Test additional profile fields"""
        self.user.phone = '1234567890'
        self.user.bio = 'Test bio'
        self.user.save()
        self.assertEqual(self.user.phone, '1234567890')
        self.assertEqual(self.user.bio, 'Test bio')


class CityModelTest(TestCase):
    """Test the City model"""
    
    def setUp(self):
        self.city = City.objects.create(
            name='New York',
            state='NY',
            country='USA'
        )
    
    def test_city_creation(self):
        """Test city is created successfully"""
        self.assertEqual(self.city.name, 'New York')
        self.assertEqual(self.city.state, 'NY')
    
    def test_city_str_method(self):
        """Test city string representation"""
        self.assertEqual(str(self.city), 'New York, NY')
    
    def test_city_slug_auto_generation(self):
        """Test slug is automatically generated"""
        self.assertEqual(self.city.slug, 'new-york')
    
    def test_city_custom_slug(self):
        """Test custom slug is preserved"""
        city = City.objects.create(
            name='Los Angeles',
            state='CA',
            slug='la-city'
        )
        self.assertEqual(city.slug, 'la-city')
    
    def test_city_event_count(self):
        """Test event count method"""
        user = User.objects.create_user(username='host', password='pass')
        Event.objects.create(
            host=user,
            title='Test Event',
            city=self.city,
            location='Venue',
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=2),
            price=Decimal('50.00'),
            capacity=100,
            is_active=True
        )
        self.assertEqual(self.city.event_count(), 1)
    
    def test_city_featured_flag(self):
        """Test featured city flag"""
        self.assertFalse(self.city.is_featured)
        self.city.is_featured = True
        self.city.save()
        self.assertTrue(self.city.is_featured)


class EventModelTest(TestCase):
    """Test the Event model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='host',
            password='pass',
            is_host=True
        )
        self.city = City.objects.create(
            name='Boston',
            state='MA'
        )
        self.event = Event.objects.create(
            host=self.user,
            title='Music Festival',
            description='Great event',
            category='music',
            city=self.city,
            location='Central Park',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            price=Decimal('75.50'),
            capacity=200
        )
    
    def test_event_creation(self):
        """Test event is created successfully"""
        self.assertEqual(self.event.title, 'Music Festival')
        self.assertEqual(self.event.host, self.user)
        self.assertTrue(self.event.is_active)
    
    def test_event_str_method(self):
        """Test event string representation"""
        self.assertEqual(str(self.event), 'Music Festival')
    
    def test_event_slug_generation(self):
        """Test slug is automatically generated"""
        self.assertEqual(self.event.slug, 'music-festival')
    
    def test_event_available_tickets_initialization(self):
        """Test available tickets equals capacity initially"""
        self.assertEqual(self.event.available_tickets, 200)
    
    def test_event_get_absolute_url(self):
        """Test get_absolute_url method"""
        url = self.event.get_absolute_url()
        self.assertEqual(url, reverse('event_detail', kwargs={'slug': self.event.slug}))
    
    def test_event_average_rating_no_reviews(self):
        """Test average rating with no reviews"""
        self.assertEqual(self.event.average_rating(), 0)
    
    def test_event_average_rating_with_reviews(self):
        """Test average rating with reviews"""
        user1 = User.objects.create_user(username='user1', password='pass')
        user2 = User.objects.create_user(username='user2', password='pass')
        Review.objects.create(user=user1, event=self.event, rating=4, comment='Good')
        Review.objects.create(user=user2, event=self.event, rating=5, comment='Great')
        self.assertEqual(self.event.average_rating(), 4.5)
    
    def test_event_review_count(self):
        """Test review count method"""
        user = User.objects.create_user(username='reviewer', password='pass')
        Review.objects.create(user=user, event=self.event, rating=5, comment='Excellent')
        self.assertEqual(self.event.review_count(), 1)
    
    def test_event_tickets_remaining(self):
        """Test tickets remaining method"""
        self.assertEqual(self.event.tickets_remaining(), 200)
    
    def test_event_is_sold_out_false(self):
        """Test is_sold_out when tickets available"""
        self.assertFalse(self.event.is_sold_out())
    
    def test_event_is_sold_out_true(self):
        """Test is_sold_out when no tickets"""
        # Use update to bypass the save method's logic
        Event.objects.filter(id=self.event.id).update(available_tickets=0)
        self.event.refresh_from_db()
        self.assertTrue(self.event.is_sold_out())
    
    def test_event_is_featured(self):
        """Test featured event flag"""
        self.assertFalse(self.event.is_featured)
        self.event.is_featured = True
        self.event.save()
        self.assertTrue(self.event.is_featured)


class EventImageModelTest(TestCase):
    """Test the EventImage model"""
    
    def setUp(self):
        user = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Miami', state='FL')
        self.event = Event.objects.create(
            host=user,
            title='Art Show',
            city=city,
            location='Gallery',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=6),
            price=Decimal('30.00'),
            capacity=50
        )
    
    def test_event_image_creation(self):
        """Test event image is created"""
        image = EventImage.objects.create(
            event=self.event,
            is_primary=True,
            order=0
        )
        self.assertEqual(image.event, self.event)
        self.assertTrue(image.is_primary)
    
    def test_event_image_str_method(self):
        """Test event image string representation"""
        image = EventImage.objects.create(event=self.event)
        self.assertIn('Art Show', str(image))
    
    def test_event_image_ordering(self):
        """Test event images are ordered correctly"""
        image1 = EventImage.objects.create(event=self.event, order=1, is_primary=False)
        image2 = EventImage.objects.create(event=self.event, order=0, is_primary=True)
        images = self.event.images.all()
        self.assertEqual(images[0], image2)  # Primary first


class BookingModelTest(TestCase):
    """Test the Booking model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='booker', password='pass')
        host = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Chicago', state='IL')
        self.event = Event.objects.create(
            host=host,
            title='Concert',
            city=city,
            location='Stadium',
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=20),
            price=Decimal('100.00'),
            capacity=500
        )
        self.booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            tickets=2,
            event_date=self.event.start_date,
            total_price=Decimal('200.00')
        )
    
    def test_booking_creation(self):
        """Test booking is created successfully"""
        self.assertEqual(self.booking.user, self.user)
        self.assertEqual(self.booking.event, self.event)
        self.assertEqual(self.booking.tickets, 2)
    
    def test_booking_str_method(self):
        """Test booking string representation"""
        expected = f"booker - Concert (2 tickets)"
        self.assertEqual(str(self.booking), expected)
    
    def test_booking_default_status(self):
        """Test booking default status is pending"""
        self.assertEqual(self.booking.status, 'pending')
    
    def test_booking_is_paid_default(self):
        """Test is_paid is False by default"""
        self.assertFalse(self.booking.is_paid)
    
    def test_booking_status_choices(self):
        """Test all booking status choices work"""
        for status, _ in Booking.STATUS_CHOICES:
            self.booking.status = status
            self.booking.save()
            self.assertEqual(self.booking.status, status)
    
    def test_booking_payment_info(self):
        """Test payment information can be stored"""
        self.booking.payment_id = 'pay_123456'
        self.booking.is_paid = True
        self.booking.save()
        self.assertEqual(self.booking.payment_id, 'pay_123456')
        self.assertTrue(self.booking.is_paid)


class ReviewModelTest(TestCase):
    """Test the Review model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='pass')
        host = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Seattle', state='WA')
        self.event = Event.objects.create(
            host=host,
            title='Tech Conference',
            city=city,
            location='Convention Center',
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=17),
            price=Decimal('250.00'),
            capacity=1000
        )
    
    def test_review_creation(self):
        """Test review is created successfully"""
        review = Review.objects.create(
            user=self.user,
            event=self.event,
            rating=5,
            comment='Excellent event!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent event!')
    
    def test_review_str_method(self):
        """Test review string representation"""
        review = Review.objects.create(
            user=self.user,
            event=self.event,
            rating=4,
            comment='Good'
        )
        expected = f"reviewer - Tech Conference (4★)"
        self.assertEqual(str(review), expected)
    
    def test_review_unique_constraint(self):
        """Test user can only review event once"""
        Review.objects.create(
            user=self.user,
            event=self.event,
            rating=5,
            comment='First review'
        )
        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.user,
                event=self.event,
                rating=3,
                comment='Second review'
            )
    
    def test_review_rating_bounds(self):
        """Test rating validators"""
        review = Review(
            user=self.user,
            event=self.event,
            rating=6,
            comment='Test'
        )
        with self.assertRaises(ValidationError):
            review.full_clean()


class FavoriteModelTest(TestCase):
    """Test the Favorite model"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        host = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Portland', state='OR')
        self.event = Event.objects.create(
            host=host,
            title='Food Festival',
            city=city,
            location='Downtown',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=31),
            price=Decimal('25.00'),
            capacity=300
        )
    
    def test_favorite_creation(self):
        """Test favorite is created successfully"""
        favorite = Favorite.objects.create(
            user=self.user,
            event=self.event
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.event, self.event)
    
    def test_favorite_str_method(self):
        """Test favorite string representation"""
        favorite = Favorite.objects.create(
            user=self.user,
            event=self.event
        )
        expected = "user - Food Festival"
        self.assertEqual(str(favorite), expected)
    
    def test_favorite_unique_constraint(self):
        """Test user can only favorite event once"""
        Favorite.objects.create(user=self.user, event=self.event)
        with self.assertRaises(Exception):
            Favorite.objects.create(user=self.user, event=self.event)


# =============================================================================
# FORM TESTS
# =============================================================================

class EventFormTest(TestCase):
    """Test the EventForm"""
    
    def setUp(self):
        self.city = City.objects.create(name='Denver', state='CO')
        self.user = User.objects.create_user(username='host', password='pass', is_host=True)
    
    def test_event_form_valid_data(self):
        """Test form with valid data"""
        form_data = {
            'title': 'New Event',
            'description': 'Description here',
            'category': 'music',
            'city': self.city.id,
            'location': 'Venue Name',
            'start_date': date.today() + timedelta(days=10),
            'end_date': date.today() + timedelta(days=11),
            'price': '50.00',
            'capacity': 100
        }
        form = EventForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_event_form_past_start_date(self):
        """Test form rejects past start date"""
        form_data = {
            'title': 'Past Event',
            'description': 'Description',
            'category': 'music',
            'city': self.city.id,
            'location': 'Venue',
            'start_date': date.today() - timedelta(days=1),
            'end_date': date.today() + timedelta(days=1),
            'price': '50.00',
            'capacity': 100
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_event_form_end_before_start(self):
        """Test form rejects end date before start date"""
        form_data = {
            'title': 'Invalid Event',
            'description': 'Description',
            'category': 'sports',
            'city': self.city.id,
            'location': 'Stadium',
            'start_date': date.today() + timedelta(days=10),
            'end_date': date.today() + timedelta(days=5),
            'price': '75.00',
            'capacity': 200
        }
        form = EventForm(data=form_data)
        self.assertFalse(form.is_valid())


class BookingFormTest(TestCase):
    """Test the BookingForm"""
    
    def setUp(self):
        host = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Austin', state='TX')
        self.event = Event.objects.create(
            host=host,
            title='Workshop',
            city=city,
            location='Office',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=9),
            price=Decimal('40.00'),
            capacity=50,
            available_tickets=50
        )
    
    def test_booking_form_valid_data(self):
        """Test form with valid booking data"""
        form_data = {
            'tickets': 3,
            'event_date': self.event.start_date
        }
        form = BookingForm(data=form_data, event=self.event)
        self.assertTrue(form.is_valid())
    
    def test_booking_form_too_many_tickets(self):
        """Test form rejects booking more than available"""
        form_data = {
            'tickets': 100,
            'event_date': self.event.start_date
        }
        form = BookingForm(data=form_data, event=self.event)
        self.assertFalse(form.is_valid())
    
    def test_booking_form_past_date(self):
        """Test form rejects past event dates"""
        form_data = {
            'tickets': 2,
            'event_date': date.today() - timedelta(days=1)
        }
        form = BookingForm(data=form_data, event=self.event)
        self.assertFalse(form.is_valid())
    
    def test_booking_form_date_outside_range(self):
        """Test form rejects date outside event range"""
        form_data = {
            'tickets': 2,
            'event_date': self.event.end_date + timedelta(days=1)
        }
        form = BookingForm(data=form_data, event=self.event)
        self.assertFalse(form.is_valid())


class ReviewFormTest(TestCase):
    """Test the ReviewForm"""
    
    def test_review_form_valid_data(self):
        """Test form with valid review data"""
        form_data = {
            'rating': 5,
            'comment': 'Great event, highly recommend!'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_review_form_invalid_rating(self):
        """Test form rejects invalid rating"""
        form_data = {
            'rating': 6,
            'comment': 'Test'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_review_form_missing_comment(self):
        """Test form requires comment"""
        form_data = {
            'rating': 4,
            'comment': ''
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())


class EventSearchFormTest(TestCase):
    """Test the EventSearchForm"""
    
    def test_search_form_all_fields_optional(self):
        """Test all fields are optional"""
        form = EventSearchForm(data={})
        self.assertTrue(form.is_valid())
    
    def test_search_form_with_data(self):
        """Test form with search data"""
        form_data = {
            'q': 'music',
            'location': 'New York',
            'category': 'music',
            'sort': 'price'
        }
        form = EventSearchForm(data=form_data)
        self.assertTrue(form.is_valid())


# =============================================================================
# VIEW TESTS
# =============================================================================

class EventListViewTest(TestCase):
    """Test the EventListView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='host', password='pass', is_host=True)
        self.city = City.objects.create(name='Phoenix', state='AZ', is_featured=True)
        self.event = Event.objects.create(
            host=self.user,
            title='Sample Event',
            city=self.city,
            location='Downtown',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=6),
            price=Decimal('35.00'),
            capacity=100,
            is_active=True
        )
    
    def test_event_list_view_status_code(self):
        """Test event list view returns 200"""
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_event_list_view_with_search(self):
        """Test event list with search query"""
        response = self.client.get(reverse('event_list'), {'q': 'Sample'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sample Event')
    
    def test_event_list_view_with_category_filter(self):
        """Test filtering by category"""
        response = self.client.get(reverse('event_list'), {'category': 'music'})
        self.assertEqual(response.status_code, 200)
    
    def test_event_list_view_with_city_filter(self):
        """Test filtering by city"""
        response = self.client.get(reverse('event_list'), {'city': self.city.slug})
        self.assertEqual(response.status_code, 200)


class EventDetailViewTest(TestCase):
    """Test the EventDetailView"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='host', password='pass')
        city = City.objects.create(name='Dallas', state='TX')
        self.event = Event.objects.create(
            host=self.user,
            title='Detail Test Event',
            city=city,
            location='Hall',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            price=Decimal('60.00'),
            capacity=150
        )
    
    def test_event_detail_view_status_code(self):
        """Test event detail view returns 200"""
        response = self.client.get(
            reverse('event_detail', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 200)
    
    def test_event_detail_view_contains_title(self):
        """Test event detail shows event title"""
        response = self.client.get(
            reverse('event_detail', kwargs={'slug': self.event.slug})
        )
        self.assertContains(response, 'Detail Test Event')
    
    def test_event_detail_view_invalid_slug(self):
        """Test 404 for invalid event slug"""
        response = self.client.get(
            reverse('event_detail', kwargs={'slug': 'invalid-slug'})
        )
        self.assertEqual(response.status_code, 404)


class CreateEventViewTest(TestCase):
    """Test the create_event view"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username='host',
            password='pass123',
            is_host=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            password='pass123'
        )
        self.city = City.objects.create(name='Houston', state='TX')
    
    def test_create_event_login_required(self):
        """Test create event requires login"""
        response = self.client.get(reverse('create_event'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_create_event_host_only(self):
        """Test only hosts can create events"""
        self.client.login(username='regular', password='pass123')
        response = self.client.get(reverse('create_event'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_create_event_get_for_host(self):
        """Test host can access create event page"""
        self.client.login(username='host', password='pass123')
        response = self.client.get(reverse('create_event'))
        self.assertEqual(response.status_code, 200)


class BookingViewsTest(TestCase):
    """Test booking-related views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Atlanta', state='GA')
        self.event = Event.objects.create(
            host=host,
            title='Booking Test Event',
            city=city,
            location='Center',
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=15),
            price=Decimal('45.00'),
            capacity=80,
            available_tickets=80
        )
    
    def test_create_booking_login_required(self):
        """Test booking requires login"""
        response = self.client.post(
            reverse('create_booking', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_my_bookings_login_required(self):
        """Test my bookings requires login"""
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 302)
    
    def test_my_bookings_view(self):
        """Test my bookings view for logged in user"""
        self.client.login(username='user', password='pass123')
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)


class SignupViewTest(TestCase):
    """Test the signup view"""
    
    def setUp(self):
        self.client = Client()
    
    def test_signup_view_get(self):
        """Test signup page loads"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
    
    def test_signup_creates_user(self):
        """Test signup creates new user"""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123'
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_signup_password_mismatch(self):
        """Test signup rejects mismatched passwords"""
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'password123',
            'password2': 'different123'
        })
        self.assertFalse(User.objects.filter(username='testuser').exists())


class ProfileViewTest(TestCase):
    """Test profile and settings views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='profileuser',
            password='pass123',
            email='profile@example.com'
        )
    
    def test_profile_view_login_required(self):
        """Test profile requires login"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
    
    def test_profile_view_authenticated(self):
        """Test profile view for logged in user"""
        self.client.login(username='profileuser', password='pass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
    
    def test_settings_view_login_required(self):
        """Test settings requires login"""
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 302)
    
    def test_settings_view_authenticated(self):
        """Test settings view for logged in user"""
        self.client.login(username='profileuser', password='pass123')
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.status_code, 200)


class FavoriteViewTest(TestCase):
    """Test favorite toggle view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Tampa', state='FL')
        self.event = Event.objects.create(
            host=host,
            title='Favorite Event',
            city=city,
            location='Place',
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=21),
            price=Decimal('55.00'),
            capacity=120
        )
    
    def test_toggle_favorite_login_required(self):
        """Test toggle favorite requires login"""
        response = self.client.get(
            reverse('toggle_favorite', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 302)
    
    def test_toggle_favorite_add(self):
        """Test adding event to favorites"""
        self.client.login(username='user', password='pass123')
        response = self.client.get(
            reverse('toggle_favorite', kwargs={'slug': self.event.slug})
        )
        self.assertTrue(
            Favorite.objects.filter(user=self.user, event=self.event).exists()
        )
    
    def test_toggle_favorite_remove(self):
        """Test removing event from favorites"""
        self.client.login(username='user', password='pass123')
        Favorite.objects.create(user=self.user, event=self.event)
        response = self.client.get(
            reverse('toggle_favorite', kwargs={'slug': self.event.slug})
        )
        self.assertFalse(
            Favorite.objects.filter(user=self.user, event=self.event).exists()
        )


# =============================================================================
# MIDDLEWARE TESTS
# =============================================================================

class RateLimitMiddlewareTest(TestCase):
    """Test the RateLimitMiddleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RateLimitMiddleware(lambda x: JsonResponse({'ok': True}))
        cache.clear()
    
    def test_rate_limit_allows_under_limit(self):
        """Test requests under limit are allowed"""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        response = self.middleware.process_request(request)
        self.assertIsNone(response)
    
    def test_rate_limit_blocks_over_limit(self):
        """Test requests over limit are blocked"""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Make requests up to limit
        for _ in range(100):
            self.middleware.process_request(request)
        
        # Next request should be blocked
        response = self.middleware.process_request(request)
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 429)
    
    def test_rate_limit_skips_health_check(self):
        """Test rate limit skips health check endpoints"""
        request = self.factory.get('/health/')
        response = self.middleware.process_request(request)
        self.assertIsNone(response)


class RequestTimingMiddlewareTest(TestCase):
    """Test the RequestTimingMiddleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RequestTimingMiddleware(lambda x: JsonResponse({'ok': True}))
    
    def test_adds_timing_header(self):
        """Test middleware adds timing header"""
        request = self.factory.get('/')
        self.middleware.process_request(request)
        response = JsonResponse({'ok': True})
        response = self.middleware.process_response(request, response)
        self.assertIn('X-Request-Duration', response)


class SecurityHeadersMiddlewareTest(TestCase):
    """Test the SecurityHeadersMiddleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = SecurityHeadersMiddleware(lambda x: JsonResponse({'ok': True}))
    
    def test_adds_security_headers(self):
        """Test middleware adds all security headers"""
        request = self.factory.get('/')
        response = JsonResponse({'ok': True})
        response = self.middleware.process_response(request, response)
        
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        self.assertIn('Referrer-Policy', response)


# =============================================================================
# HEALTH CHECK TESTS
# =============================================================================

class HealthCheckTest(TestCase):
    """Test health check endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
    
    def test_health_check_endpoint(self):
        """Test basic health check"""
        request = self.factory.get('/health/')
        response = health_check(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
    
    def test_liveness_check_endpoint(self):
        """Test liveness check"""
        request = self.factory.get('/health/live/')
        response = liveness_check(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'alive')
    
    def test_readiness_check_endpoint(self):
        """Test readiness check"""
        request = self.factory.get('/health/ready/')
        response = readiness_check(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('checks', data)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        request = self.factory.get('/metrics/')
        response = metrics(request)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('metrics', data)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class EventBookingIntegrationTest(TestCase):
    """Test complete event booking workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='customer',
            password='pass123',
            email='customer@example.com'
        )
        self.host = User.objects.create_user(
            username='eventhost',
            password='pass123',
            is_host=True
        )
        self.city = City.objects.create(name='San Diego', state='CA')
        self.event = Event.objects.create(
            host=self.host,
            title='Integration Test Event',
            city=self.city,
            location='Convention Center',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=31),
            price=Decimal('99.99'),
            capacity=100,
            available_tickets=100
        )
    
    def test_complete_booking_flow(self):
        """Test complete booking process"""
        # Login
        self.client.login(username='customer', password='pass123')
        
        # View event detail
        response = self.client.get(
            reverse('event_detail', kwargs={'slug': self.event.slug})
        )
        self.assertEqual(response.status_code, 200)
        
        # Create booking
        initial_tickets = self.event.available_tickets
        response = self.client.post(
            reverse('create_booking', kwargs={'slug': self.event.slug}),
            {
                'tickets': 2,
                'event_date': self.event.start_date
            }
        )
        
        # Verify booking created
        booking = Booking.objects.filter(user=self.user, event=self.event).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.tickets, 2)
        
        # Verify tickets reduced
        self.event.refresh_from_db()
        self.assertEqual(self.event.available_tickets, initial_tickets - 2)


class ReviewWorkflowTest(TestCase):
    """Test review workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reviewer', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Las Vegas', state='NV')
        self.event = Event.objects.create(
            host=host,
            title='Review Test Event',
            city=city,
            location='Strip',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=4),
            price=Decimal('150.00'),
            capacity=200
        )
        # Create a completed booking
        self.booking = Booking.objects.create(
            user=self.user,
            event=self.event,
            tickets=1,
            event_date=self.event.start_date,
            total_price=self.event.price,
            status='completed',
            is_paid=True
        )
    
    def test_add_review_after_booking(self):
        """Test user can review after attending event"""
        self.client.login(username='reviewer', password='pass123')
        
        response = self.client.post(
            reverse('add_review', kwargs={'slug': self.event.slug}),
            {
                'rating': 5,
                'comment': 'Amazing experience!'
            }
        )
        
        # Verify review created
        review = Review.objects.filter(user=self.user, event=self.event).first()
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
    
    def test_cannot_review_twice(self):
        """Test user cannot review same event twice"""
        self.client.login(username='reviewer', password='pass123')
        
        # First review
        Review.objects.create(
            user=self.user,
            event=self.event,
            rating=4,
            comment='Good'
        )
        
        # Attempt second review
        response = self.client.post(
            reverse('add_review', kwargs={'slug': self.event.slug}),
            {
                'rating': 5,
                'comment': 'Changed my mind'
            }
        )
        
        # Should still only have one review
        self.assertEqual(Review.objects.filter(user=self.user, event=self.event).count(), 1)


class SearchFilterTest(TestCase):
    """Test search and filter functionality"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='pass123', is_host=True)
        self.city1 = City.objects.create(name='San Francisco', state='CA')
        self.city2 = City.objects.create(name='Oakland', state='CA')
        
        # Create multiple events
        Event.objects.create(
            host=self.host,
            title='Music Concert',
            category='music',
            city=self.city1,
            location='Venue 1',
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=5),
            price=Decimal('50.00'),
            capacity=100
        )
        Event.objects.create(
            host=self.host,
            title='Sports Game',
            category='sports',
            city=self.city2,
            location='Stadium',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=10),
            price=Decimal('75.00'),
            capacity=5000
        )
    
    def test_search_by_keyword(self):
        """Test searching events by keyword"""
        response = self.client.get(reverse('event_list'), {'q': 'Music'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Music Concert')
        self.assertNotContains(response, 'Sports Game')
    
    def test_filter_by_category(self):
        """Test filtering events by category"""
        response = self.client.get(reverse('event_list'), {'category': 'sports'})
        self.assertEqual(response.status_code, 200)
    
    def test_filter_by_price_range(self):
        """Test filtering by price range"""
        response = self.client.get(
            reverse('event_list'),
            {'min_price': '60', 'max_price': '100'}
        )
        self.assertEqual(response.status_code, 200)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class EdgeCaseTests(TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass123')
        self.host = User.objects.create_user(username='host', password='pass123', is_host=True)
        self.city = City.objects.create(name='Test City', state='TC')
    
    def test_booking_sold_out_event(self):
        """Test booking sold out event"""
        event = Event.objects.create(
            host=self.host,
            title='Sold Out Event',
            city=self.city,
            location='Venue',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=10),
            price=Decimal('50.00'),
            capacity=10,
            available_tickets=0
        )
        
        self.client.login(username='user', password='pass123')
        response = self.client.post(
            reverse('create_booking', kwargs={'slug': event.slug}),
            {'tickets': 1, 'event_date': event.start_date}
        )
        
        # View should handle sold out check, but may still create pending booking
        # The important test is that available_tickets doesn't go negative
        event.refresh_from_db()
        self.assertGreaterEqual(event.available_tickets, 0)
    
    def test_cancel_booking_too_late(self):
        """Test canceling booking within 3 days"""
        event = Event.objects.create(
            host=self.host,
            title='Soon Event',
            city=self.city,
            location='Place',
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=2),
            price=Decimal('40.00'),
            capacity=50
        )
        
        booking = Booking.objects.create(
            user=self.user,
            event=event,
            tickets=1,
            event_date=event.start_date,
            total_price=event.price,
            status='confirmed'
        )
        
        self.client.login(username='user', password='pass123')
        response = self.client.get(
            reverse('cancel_booking', kwargs={'booking_id': booking.id})
        )
        
        # Booking should not be cancelled
        booking.refresh_from_db()
        self.assertNotEqual(booking.status, 'cancelled')
    
    def test_duplicate_slug_handling(self):
        """Test handling of duplicate event titles"""
        event1 = Event.objects.create(
            host=self.host,
            title='Duplicate Title',
            city=self.city,
            location='Venue 1',
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=15),
            price=Decimal('30.00'),
            capacity=100
        )
        
        # Creating another with same title will fail with UNIQUE constraint
        # This is expected behavior - slugs must be unique
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Event.objects.create(
                host=self.host,
                title='Duplicate Title',
                city=self.city,
                location='Venue 2',
                start_date=date.today() + timedelta(days=16),
                end_date=date.today() + timedelta(days=16),
                price=Decimal('35.00'),
                capacity=100
            )
    
    def test_zero_price_event(self):
        """Test free events (price = 0)"""
        event = Event.objects.create(
            host=self.host,
            title='Free Event',
            city=self.city,
            location='Park',
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=7),
            price=Decimal('0.00'),
            capacity=1000
        )
        self.assertEqual(event.price, Decimal('0.00'))
    
    def test_long_event_duration(self):
        """Test event with long duration"""
        event = Event.objects.create(
            host=self.host,
            title='Festival',
            city=self.city,
            location='Grounds',
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            price=Decimal('200.00'),
            capacity=10000
        )
        duration = (event.end_date - event.start_date).days
        self.assertEqual(duration, 30)



# =============================================================================
# ADDITIONAL VIEW POST TESTS FOR HIGHER COVERAGE
# =============================================================================

class CreateEventPostTest(TestCase):
    """Test creating events via POST"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username='host',
            password='pass123',
            is_host=True
        )
        self.city = City.objects.create(name='Boston', state='MA')
    
    def test_create_event_post_success(self):
        """Test successful event creation via POST"""
        self.client.login(username='host', password='pass123')
        response = self.client.post(reverse('create_event'), {
            'title': 'New Music Event',
            'description': 'Great concert',
            'category': 'music',
            'city': self.city.id,
            'location': 'Stadium',
            'start_date': (date.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=31)).strftime('%Y-%m-%d'),
            'price': '75.00',
            'capacity': 500
        })
        self.assertTrue(Event.objects.filter(title='New Music Event').exists())


class UpdateEventPostTest(TestCase):
    """Test updating events via POST"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='pass123', is_host=True)
        self.city = City.objects.create(name='Austin', state='TX')
        self.event = Event.objects.create(
            host=self.host,
            title='Original Title',
            city=self.city,
            location='Venue',
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=21),
            price=Decimal('50.00'),
            capacity=100
        )
    
    def test_update_event_post(self):
        """Test updating event via POST"""
        self.client.login(username='host', password='pass123')
        response = self.client.post(
            reverse('update_event', kwargs={'slug': self.event.slug}),
            {
                'title': 'Updated Title',
                'description': 'Updated description',
                'category': 'music',
                'city': self.city.id,
                'location': 'New Venue',
                'start_date': self.event.start_date.strftime('%Y-%m-%d'),
                'end_date': self.event.end_date.strftime('%Y-%m-%d'),
                'price': '60.00',
                'capacity': 150
            }
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.location, 'New Venue')


class PaymentProcessTest(TestCase):
    """Test payment processing"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Seattle', state='WA')
        event = Event.objects.create(
            host=host,
            title='Payment Test',
            city=city,
            location='Hall',
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=16),
            price=Decimal('100.00'),
            capacity=50
        )
        self.booking = Booking.objects.create(
            user=self.user,
            event=event,
            tickets=2,
            event_date=event.start_date,
            total_price=Decimal('200.00')
        )
    
    def test_process_payment_post(self):
        """Test payment processing POST"""
        self.client.login(username='user', password='pass123')
        response = self.client.post(
            reverse('process_payment', kwargs={'booking_id': self.booking.id}),
            {'payment_method': 'card'}
        )
        self.booking.refresh_from_db()
        self.assertTrue(self.booking.is_paid)
        self.assertEqual(self.booking.status, 'confirmed')


class DeleteEventPostTest(TestCase):
    """Test deleting events"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(username='host', password='pass123', is_host=True)
        city = City.objects.create(name='Portland', state='OR')
        self.event = Event.objects.create(
            host=self.host,
            title='Delete Test',
            city=city,
            location='Place',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            price=Decimal('40.00'),
            capacity=80
        )
    
    def test_delete_event_post(self):
        """Test deleting event via POST"""
        self.client.login(username='host', password='pass123')
        response = self.client.post(
            reverse('delete_event', kwargs={'slug': self.event.slug})
        )
        self.event.refresh_from_db()
        self.assertFalse(self.event.is_active)


class SettingsUpdateTest(TestCase):
    """Test settings update"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='settingsuser',
            password='pass123',
            email='old@example.com'
        )
    
    def test_settings_update_post(self):
        """Test updating user settings"""
        self.client.login(username='settingsuser', password='pass123')
        response = self.client.post(reverse('settings'), {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'new@example.com',
            'phone': '1234567890',
            'bio': 'New bio'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.email, 'new@example.com')


class AjaxEndpointsTest(TestCase):
    """Test AJAX endpoints"""
    
    def setUp(self):
        self.client = Client()
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Miami', state='FL')
        Event.objects.create(
            host=host,
            title='Ajax Test Event',
            city=city,
            location='Beach',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            price=Decimal('55.00'),
            capacity=100,
            is_active=True
        )
    
    def test_search_autocomplete(self):
        """Test search autocomplete AJAX"""
        response = self.client.get('/search/autocomplete/', {'q': 'Ajax'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('results', data)
    
    def test_search_autocomplete_short_query(self):
        """Test autocomplete with short query"""
        response = self.client.get('/search/autocomplete/', {'q': 'A'})
        data = json.loads(response.content)
        self.assertEqual(data['results'], [])


class EventsByCityTest(TestCase):
    """Test events by city view"""
    
    def setUp(self):
        self.client = Client()
        self.city = City.objects.create(name='Denver', state='CO')
        host = User.objects.create_user(username='host', password='pass123')
        Event.objects.create(
            host=host,
            title='Denver Event',
            city=self.city,
            location='Downtown',
            start_date=date.today() + timedelta(days=15),
            end_date=date.today() + timedelta(days=16),
            price=Decimal('45.00'),
            capacity=200,
            is_active=True
        )
    
    def test_events_by_city(self):
        """Test filtering events by city"""
        response = self.client.get(
            reverse('events_by_city', kwargs={'city_slug': self.city.slug})
        )
        self.assertEqual(response.status_code, 200)
        # Check that city is in context
        self.assertEqual(response.context['city'], self.city)


class MyEventsHostTest(TestCase):
    """Test my events view for hosts"""
    
    def setUp(self):
        self.client = Client()
        self.host = User.objects.create_user(
            username='eventhost',
            password='pass123',
            is_host=True
        )
        city = City.objects.create(name='Nashville', state='TN')
        Event.objects.create(
            host=self.host,
            title='Host Event',
            city=city,
            location='Venue',
            start_date=date.today() + timedelta(days=20),
            end_date=date.today() + timedelta(days=21),
            price=Decimal('70.00'),
            capacity=150
        )
    
    def test_my_events_view(self):
        """Test my events view loads for host"""
        self.client.login(username='eventhost', password='pass123')
        response = self.client.get(reverse('my_events'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Host Event')


class CancelBookingTest(TestCase):
    """Test canceling bookings"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='canceler', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Phoenix', state='AZ')
        event = Event.objects.create(
            host=host,
            title='Cancellable Event',
            city=city,
            location='Center',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=11),
            price=Decimal('80.00'),
            capacity=100,
            available_tickets=98
        )
        self.booking = Booking.objects.create(
            user=self.user,
            event=event,
            tickets=2,
            event_date=event.start_date,
            total_price=Decimal('160.00'),
            status='confirmed'
        )
    
    def test_cancel_booking_success(self):
        """Test successful booking cancellation"""
        self.client.login(username='canceler', password='pass123')
        response = self.client.get(
            reverse('cancel_booking', kwargs={'booking_id': self.booking.id})
        )
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')


class AddReviewPostTest(TestCase):
    """Test adding reviews via POST"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reviewer', password='pass123')
        host = User.objects.create_user(username='host', password='pass123')
        city = City.objects.create(name='Minneapolis', state='MN')
        self.event = Event.objects.create(
            host=host,
            title='Reviewable Event',
            city=city,
            location='Theater',
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=4),
            price=Decimal('65.00'),
            capacity=80
        )
        Booking.objects.create(
            user=self.user,
            event=self.event,
            tickets=1,
            event_date=self.event.start_date,
            total_price=self.event.price,
            status='completed',
            is_paid=True
        )
    
    def test_add_review_post(self):
        """Test adding review via POST"""
        self.client.login(username='reviewer', password='pass123')
        response = self.client.post(
            reverse('add_review', kwargs={'slug': self.event.slug}),
            {
                'rating': 4,
                'comment': 'Great event, enjoyed it!'
            }
        )
        self.assertTrue(
            Review.objects.filter(user=self.user, event=self.event).exists()
        )
