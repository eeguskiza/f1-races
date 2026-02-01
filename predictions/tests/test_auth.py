from django.test import TestCase
from django.contrib.auth.models import User

from predictions.forms import SignupForm
from predictions.models import NewsPost


class SignupFormTests(TestCase):
    """Tests for the SignupForm."""

    def test_signup_form_valid(self):
        """Test signup form with valid data."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = SignupForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_signup_form_rejects_duplicate_email(self):
        """Test that signup form rejects duplicate email (case-insensitive)."""
        # Create existing user with email
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="password123"
        )

        # Try to create another user with same email (different case)
        form_data = {
            "username": "newuser",
            "email": "TEST@EXAMPLE.COM",  # Same email, different case
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_requires_email(self):
        """Test that email is required."""
        form_data = {
            "username": "testuser",
            "email": "",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_signup_form_password_mismatch(self):
        """Test that mismatched passwords are rejected."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "SecurePass123!",
            "password2": "DifferentPass456!",
        }
        form = SignupForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class NewsPostModelTests(TestCase):
    """Tests for the NewsPost model."""

    def test_newspost_has_image_url_field(self):
        """Test that NewsPost has image_url field."""
        news = NewsPost.objects.create(
            title="Test News",
            body="Test body content",
            image_url="https://example.com/image.jpg"
        )
        self.assertEqual(news.image_url, "https://example.com/image.jpg")

    def test_newspost_image_url_optional(self):
        """Test that image_url is optional."""
        news = NewsPost.objects.create(
            title="Test News Without Image",
            body="Test body content"
        )
        self.assertEqual(news.image_url, "")

    def test_newspost_str(self):
        """Test NewsPost string representation."""
        news = NewsPost.objects.create(
            title="Breaking News",
            body="Content here"
        )
        self.assertEqual(str(news), "Breaking News")
