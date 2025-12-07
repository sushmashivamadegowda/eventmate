from django.core.management.base import BaseCommand
from myapp.models import User, Event, City, EventImage
from datetime import datetime, date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample events in Music and Sports categories'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate sample events...')
        
        # Create or get host user
        host, created = User.objects.get_or_create(
            username='event_host',
            defaults={
                'email': 'host@events.com',
                'first_name': 'Event',
                'last_name': 'Host',
                'is_host': True,
            }
        )
        if created:
            host.set_password('password123')
            host.save()
            self.stdout.write(self.style.SUCCESS('Created host user: event_host/password123'))
        else:
            self.stdout.write('Host user already exists')

        # Create or get cities
        cities_data = [
            {'name': 'New York', 'state': 'NY', 'country': 'USA'},
            {'name': 'Los Angeles', 'state': 'CA', 'country': 'USA'},
            {'name': 'Chicago', 'state': 'IL', 'country': 'USA'},
            {'name': 'Miami', 'state': 'FL', 'country': 'USA'},
        ]
        
        cities = []
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                name=city_data['name'],
                defaults=city_data
            )
            cities.append(city)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created city: {city.name}'))
            else:
                self.stdout.write(f'City {city.name} already exists')

        # Sample events data
        events_data = [
            # Music Events
            {
                'title': 'Summer Jazz Festival 2025',
                'category': 'music',
                'description': 'An electrifying evening of smooth jazz featuring renowned artists from around the world. Experience the golden age of jazz with modern twists.',
                'location': 'Central Park Amphitheater',
                'city_index': 0,
                'start_date': date.today() + timedelta(days=30),
                'end_date': date.today() + timedelta(days=32),
                'start_time': '19:00',
                'price': Decimal('75.00'),
                'capacity': 500,
                'included': 'Welcome drink, Program booklet, Meet & greet opportunity',
                'things_to_know': 'Outdoor event - weather permitting. Bring light jacket.',
                'cancellation_policy': 'Full refund up to 48 hours before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'Rock Legends Concert',
                'category': 'music',
                'description': 'An explosive night featuring classic rock covers and original hits from the greatest rock bands of all time.',
                'location': 'Madison Square Garden',
                'city_index': 0,
                'start_date': date.today() + timedelta(days=45),
                'end_date': date.today() + timedelta(days=45),
                'start_time': '20:00',
                'price': Decimal('120.00'),
                'capacity': 2000,
                'included': 'Concert ticket, Merchandise voucher, Bar access',
                'things_to_know': 'Standing room event. Arrive early for best spots.',
                'cancellation_policy': 'No refunds, but tickets can be transferred.',
                'age_restriction': '18+ only',
                'is_featured': True
            },
            {
                'title': 'Classical Symphony Night',
                'category': 'music',
                'description': 'Experience the timeless beauty of classical music with a full symphony orchestra performing Beethoven and Mozart masterpieces.',
                'location': 'Walt Disney Concert Hall',
                'city_index': 1,
                'start_date': date.today() + timedelta(days=60),
                'end_date': date.today() + timedelta(days=60),
                'start_time': '19:30',
                'price': Decimal('85.00'),
                'capacity': 800,
                'included': 'Concert program, Pre-concert discussion, Refreshments',
                'things_to_know': 'Formal attire recommended. Silence phones during performance.',
                'cancellation_policy': 'Full refund up to 72 hours before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
            },
            
            # Sports Events
            {
                'title': 'NBA Championship Game',
                'category': 'sports',
                'description': 'Witness basketball history in the making! Two top teams compete for the ultimate prize in a thrilling championship game.',
                'location': 'Staples Center',
                'city_index': 1,
                'start_date': date.today() + timedelta(days=35),
                'end_date': date.today() + timedelta(days=35),
                'start_time': '19:00',
                'price': Decimal('200.00'),
                'capacity': 19000,
                'included': 'Game ticket, Team program, Halftime entertainment access',
                'things_to_know': 'No outside food/beverages. Parking available for additional fee.',
                'cancellation_policy': 'Tickets non-refundable, rain or shine event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'Marathon Championship',
                'category': 'sports',
                'description': 'Join thousands of runners in the city\'s biggest marathon! Choose from full marathon, half marathon, or 5K options.',
                'location': 'Grant Park',
                'city_index': 2,
                'start_date': date.today() + timedelta(days=90),
                'end_date': date.today() + timedelta(days=90),
                'start_time': '06:00',
                'price': Decimal('50.00'),
                'capacity': 5000,
                'included': 'Race registration, Finisher medal, Post-race refreshments, Timing chip',
                'things_to_know': 'Early start time. Transportation from start to finish provided.',
                'cancellation_policy': '50% refund up to 2 weeks before event.',
                'age_restriction': '16+ for marathon, all ages for 5K',
                'is_featured': False
            },
            {
                'title': 'UFC Fight Night',
                'category': 'sports',
                'description': 'Experience the ultimate mixed martial arts event featuring top fighters in intense championship bouts.',
                'location': 'American Airlines Arena',
                'city_index': 3,
                'start_date': date.today() + timedelta(days=25),
                'end_date': date.today() + timedelta(days=25),
                'start_time': '18:00',
                'price': Decimal('150.00'),
                'capacity': 15000,
                'included': 'Fight ticket, Pre-fight show access, Official program',
                'things_to_know': 'Expect intense action. Arrive early for fighter introductions.',
                'cancellation_policy': 'No refunds, event proceeds rain or shine.',
                'age_restriction': '18+ only',
                'is_featured': True
            }
        ]

        # Create events
        created_count = 0
        for event_data in events_data:
            # Check if event already exists
            if Event.objects.filter(title=event_data['title']).exists():
                self.stdout.write(f'Event "{event_data["title"]}" already exists, skipping...')
                continue
            
            city = cities[event_data['city_index']]
            event = Event.objects.create(
                host=host,
                title=event_data['title'],
                description=event_data['description'],
                category=event_data['category'],
                city=city,
                location=event_data['location'],
                start_date=event_data['start_date'],
                end_date=event_data['end_date'],
                start_time=event_data['start_time'],
                price=event_data['price'],
                capacity=event_data['capacity'],
                available_tickets=event_data['capacity'],
                included=event_data['included'],
                things_to_know=event_data['things_to_know'],
                cancellation_policy=event_data['cancellation_policy'],
                age_restriction=event_data['age_restriction'],
                is_featured=event_data['is_featured'],
                is_active=True
            )
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'Created event: {event.title} ({event.category})'))

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} new events!\n'
                f'Summary:\n'
                f'- Host user: event_host (password: password123)\n'
                f'- Cities: {len(cities)} cities available\n'
                f'- Events: Music and Sports categories populated\n'
                f'Run "python manage.py runserver" and visit your site to see the events!'
            )
        )