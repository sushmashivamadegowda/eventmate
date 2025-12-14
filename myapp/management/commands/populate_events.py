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
            {'name': 'Mumbai', 'state': 'Maharashtra', 'country': 'India'},
            {'name': 'Delhi', 'state': 'Delhi', 'country': 'India'},
            {'name': 'Bangalore', 'state': 'Karnataka', 'country': 'India'},
            {'name': 'Chennai', 'state': 'Tamil Nadu', 'country': 'India'},
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
            },
            
            # Technology Events in India
            {
                'title': 'Python Developer Summit Mumbai 2025',
                'category': 'tech',
                'description': 'Join India\'s largest Python conference featuring workshops, talks, and networking with Python experts. Learn about Django, Flask, Data Science, ML, and more.',
                'location': 'NSCI Dome, Worli',
                'city_index': 4,  # Mumbai
                'start_date': date.today() + timedelta(days=40),
                'end_date': date.today() + timedelta(days=42),
                'start_time': '09:00',
                'price': Decimal('2500.00'),
                'capacity': 1500,
                'included': 'Conference pass, Workshop access, Lunch & snacks, Swag bag, Certificate',
                'things_to_know': 'Bring your laptop for hands-on workshops. Wi-Fi provided.',
                'cancellation_policy': 'Full refund up to 7 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'JavaScript & React Bootcamp Delhi',
                'category': 'tech',
                'description': 'Intensive 3-day bootcamp covering modern JavaScript, React, Node.js, and full-stack development. Perfect for beginners and intermediate developers.',
                'location': 'India Habitat Centre, Lodhi Road',
                'city_index': 5,  # Delhi
                'start_date': date.today() + timedelta(days=50),
                'end_date': date.today() + timedelta(days=52),
                'start_time': '10:00',
                'price': Decimal('3000.00'),
                'capacity': 800,
                'included': 'Training materials, Project assignments, Certificate, Networking dinner',
                'things_to_know': 'Basic programming knowledge required. Laptop mandatory.',
                'cancellation_policy': '50% refund up to 5 days before event.',
                'age_restriction': '16+ recommended',
                'is_featured': True
            },
            {
                'title': 'GitHub Universe India - Bangalore',
                'category': 'tech',
                'description': 'GitHub\'s official event in India! Learn about Git workflows, GitHub Actions, Copilot, open source collaboration, and DevOps best practices.',
                'location': 'Bangalore International Exhibition Centre',
                'city_index': 6,  # Bangalore
                'start_date': date.today() + timedelta(days=65),
                'end_date': date.today() + timedelta(days=66),
                'start_time': '09:30',
                'price': Decimal('1500.00'),
                'capacity': 2000,
                'included': 'Conference pass, GitHub swag, Meals, Workshops, Networking sessions',
                'things_to_know': 'GitHub account recommended. Hands-on sessions available.',
                'cancellation_policy': 'Full refund up to 10 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'Python for Data Science Chennai',
                'category': 'tech',
                'description': 'Master Python for data analysis, visualization, and machine learning. Hands-on workshop with real-world datasets using pandas, NumPy, and scikit-learn.',
                'location': 'IIT Madras Research Park',
                'city_index': 7,  # Chennai
                'start_date': date.today() + timedelta(days=55),
                'end_date': date.today() + timedelta(days=56),
                'start_time': '09:00',
                'price': Decimal('2000.00'),
                'capacity': 500,
                'included': 'Workshop materials, Dataset access, Certificate, Refreshments',
                'things_to_know': 'Python basics required. Bring laptop with Python installed.',
                'cancellation_policy': 'Full refund up to 14 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
            },
            {
                'title': 'Full Stack JavaScript Hackathon Mumbai',
                'category': 'tech',
                'description': '48-hour coding marathon! Build innovative web applications using MERN stack. Amazing prizes, mentorship from industry experts, and networking opportunities.',
                'location': 'WeWork BKC, Bandra Kurla Complex',
                'city_index': 4,  # Mumbai
                'start_date': date.today() + timedelta(days=75),
                'end_date': date.today() + timedelta(days=77),
                'start_time': '08:00',
                'price': Decimal('500.00'),
                'capacity': 300,
                'included': 'Meals throughout, Energy drinks, Mentorship, Prizes worth ₹5 lakhs',
                'things_to_know': '48-hour event. Can form teams up to 4 members. Sleeping area provided.',
                'cancellation_policy': 'No refund after registration confirmation.',
                'age_restriction': '18+ only',
                'is_featured': True
            },
            {
                'title': 'Advanced Python & Django Workshop Delhi',
                'category': 'tech',
                'description': 'Deep dive into advanced Python concepts and Django framework. Build scalable web applications, REST APIs, and learn deployment strategies.',
                'location': 'Aerocity Convention Centre',
                'city_index': 5,  # Delhi
                'start_date': date.today() + timedelta(days=80),
                'end_date': date.today() + timedelta(days=81),
                'start_time': '10:00',
                'price': Decimal('2800.00'),
                'capacity': 600,
                'included': 'Workshop access, Code repository, Certificate, Lunch',
                'things_to_know': 'Intermediate Python knowledge required. Django basics helpful.',
                'cancellation_policy': 'Full refund up to 7 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
            },
            {
                'title': 'GitHub Open Source Summit Bangalore',
                'category': 'tech',
                'description': 'Celebrate open source! Connect with maintainers, contribute to projects, learn best practices for collaboration, and discover career opportunities in OSS.',
                'location': 'Sheraton Grand Bangalore Hotel',
                'city_index': 6,  # Bangalore
                'start_date': date.today() + timedelta(days=85),
                'end_date': date.today() + timedelta(days=85),
                'start_time': '09:00',
                'price': Decimal('1000.00'),
                'capacity': 1200,
                'included': 'Summit pass, GitHub premium trial, Swag, Lunch & snacks',
                'things_to_know': 'Bring ideas for collaboration. Networking sessions included.',
                'cancellation_policy': 'Full refund up to 5 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'React & JavaScript Masterclass Chennai',
                'category': 'tech',
                'description': 'Comprehensive React training covering hooks, state management, Redux, testing, and modern JavaScript ES6+. Build production-ready applications.',
                'location': 'Chennai Trade Centre, Nandambakkam',
                'city_index': 7,  # Chennai
                'start_date': date.today() + timedelta(days=70),
                'end_date': date.today() + timedelta(days=72),
                'start_time': '09:30',
                'price': Decimal('3500.00'),
                'capacity': 400,
                'included': 'Training kit, Project source code, Certificate, Tea & snacks',
                'things_to_know': 'JavaScript fundamentals required. React basics helpful but not mandatory.',
                'cancellation_policy': '50% refund up to 10 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
            },
            {
                'title': 'Python AI/ML Conference Mumbai',
                'category': 'tech',
                'description': 'Explore cutting-edge AI and Machine Learning with Python. Sessions on TensorFlow, PyTorch, NLP, Computer Vision, and real-world AI applications.',
                'location': 'Jio World Convention Centre, BKC',
                'city_index': 4,  # Mumbai
                'start_date': date.today() + timedelta(days=95),
                'end_date': date.today() + timedelta(days=97),
                'start_time': '09:00',
                'price': Decimal('4000.00'),
                'capacity': 1800,
                'included': 'Conference pass, Workshop sessions, Research papers, Meals, Certificate',
                'things_to_know': 'Python and basic ML knowledge recommended. GPU access provided for workshops.',
                'cancellation_policy': 'Full refund up to 14 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'JavaScript Framework Battle Delhi',
                'category': 'tech',
                'description': 'Compare and learn React, Vue, and Angular in one event! Build the same app in all three frameworks and decide which suits your needs best.',
                'location': 'Pragati Maidan Convention Centre',
                'city_index': 5,  # Delhi
                'start_date': date.today() + timedelta(days=88),
                'end_date': date.today() + timedelta(days=89),
                'start_time': '10:00',
                'price': Decimal('2200.00'),
                'capacity': 700,
                'included': 'Workshop materials, Code samples, Certificate, Refreshments',
                'things_to_know': 'Solid JavaScript knowledge required. Familiarity with any framework helpful.',
                'cancellation_policy': 'Full refund up to 7 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
            },
            {
                'title': 'GitHub Actions & DevOps Bangalore',
                'category': 'tech',
                'description': 'Master CI/CD with GitHub Actions! Learn automation, testing pipelines, deployment strategies, and DevOps best practices for modern development.',
                'location': 'The Leela Palace, Old Airport Road',
                'city_index': 6,  # Bangalore
                'start_date': date.today() + timedelta(days=92),
                'end_date': date.today() + timedelta(days=93),
                'start_time': '09:00',
                'price': Decimal('2600.00'),
                'capacity': 900,
                'included': 'Training materials, GitHub Enterprise trial, Certificate, Meals',
                'things_to_know': 'Basic Git knowledge required. DevOps concepts helpful.',
                'cancellation_policy': 'Full refund up to 10 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': True
            },
            {
                'title': 'Python Web Scraping & Automation Chennai',
                'category': 'tech',
                'description': 'Learn web scraping with BeautifulSoup, Selenium, and Scrapy. Automate repetitive tasks and extract data from websites efficiently and ethically.',
                'location': 'Anna Centenary Library, Kotturpuram',
                'city_index': 7,  # Chennai
                'start_date': date.today() + timedelta(days=100),
                'end_date': date.today() + timedelta(days=100),
                'start_time': '10:00',
                'price': Decimal('1800.00'),
                'capacity': 350,
                'included': 'Workshop kit, Code samples, Practice datasets, Certificate',
                'things_to_know': 'Python basics required. Bring laptop with Python installed.',
                'cancellation_policy': 'Full refund up to 5 days before event.',
                'age_restriction': 'All ages welcome',
                'is_featured': False
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