# FinalEventMate

An event management platform built with Django, allowing users to create, book, and review events.

## Features

- **User Management**: Custom user model with host capabilities, profiles, and authentication.
- **Event Creation**: Hosts can create events with details like category, location, pricing, and capacity.
- **Booking System**: Users can book tickets for events with payment integration.
- **Reviews and Ratings**: Users can leave reviews and ratings for events.
- **Favorites**: Users can add events to their favorites/wishlist.
- **City Management**: Events are organized by cities with featured cities.
- **Media Upload**: Image uploads for events and user profiles using Cloudinary.
- **Admin Panel**: Django admin interface for managing content.

## Technologies Used

- **Backend**: Django 5.2.5
- **Database**: SQLite (default), configurable for other databases
- **Media Storage**: Cloudinary
- **Frontend**: HTML, CSS, JavaScript (via Django templates)
- **Authentication**: Django's built-in authentication system

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd finaleventmate
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install django cloudinary
   ```

4. **Apply migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:8000/`
   - Admin panel: `http://127.0.0.1:8000/admin/`

## Configuration

- **Cloudinary Settings**: Update the Cloudinary credentials in `finaleventmate/settings.py` for media uploads.
- **Database**: Modify `DATABASES` in `settings.py` to use a different database if needed.
- **Secret Key**: Change the `SECRET_KEY` in `settings.py` for production.

## Usage

1. **Register/Login**: Create an account or log in.
2. **Browse Events**: View events by category or city.
3. **Create Events**: If you're a host, create new events.
4. **Book Events**: Purchase tickets for events.
5. **Manage Bookings**: View your bookings and event history.
6. **Leave Reviews**: Rate and review events you've attended.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Submit a pull request.

## License

This project is licensed under the MIT License.