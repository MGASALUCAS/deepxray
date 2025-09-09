from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from collections import defaultdict


class Command(BaseCommand):
    help = 'Check for duplicate users and provide recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix duplicate users by keeping the first one',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking for duplicate users...'))
        
        # Check for duplicate usernames
        username_counts = defaultdict(list)
        email_counts = defaultdict(list)
        
        for user in User.objects.all():
            username_counts[user.username].append(user)
            email_counts[user.email].append(user)
        
        # Report duplicate usernames
        duplicate_usernames = {k: v for k, v in username_counts.items() if len(v) > 1}
        if duplicate_usernames:
            self.stdout.write(
                self.style.WARNING(f'Found {len(duplicate_usernames)} duplicate usernames:')
            )
            for username, users in duplicate_usernames.items():
                self.stdout.write(f'  Username "{username}": {len(users)} users')
                for user in users:
                    self.stdout.write(f'    - ID: {user.id}, Email: {user.email}, Date: {user.date_joined}')
        
        # Report duplicate emails
        duplicate_emails = {k: v for k, v in email_counts.items() if len(v) > 1}
        if duplicate_emails:
            self.stdout.write(
                self.style.WARNING(f'Found {len(duplicate_emails)} duplicate emails:')
            )
            for email, users in duplicate_emails.items():
                self.stdout.write(f'  Email "{email}": {len(users)} users')
                for user in users:
                    self.stdout.write(f'    - ID: {user.id}, Username: {user.username}, Date: {user.date_joined}')
        
        if not duplicate_usernames and not duplicate_emails:
            self.stdout.write(self.style.SUCCESS('No duplicate users found!'))
            return
        
        # Fix duplicates if requested
        if options['fix']:
            self.stdout.write(self.style.WARNING('Fixing duplicate users...'))
            
            # Fix duplicate usernames
            for username, users in duplicate_usernames.items():
                # Keep the first user, delete the rest
                users_to_delete = users[1:]
                for user in users_to_delete:
                    self.stdout.write(f'  Deleting duplicate user: ID {user.id} (username: {user.username})')
                    user.delete()
            
            # Fix duplicate emails
            for email, users in duplicate_emails.items():
                # Keep the first user, delete the rest
                users_to_delete = users[1:]
                for user in users_to_delete:
                    self.stdout.write(f'  Deleting duplicate user: ID {user.id} (email: {user.email})')
                    user.delete()
            
            self.stdout.write(self.style.SUCCESS('Duplicate users fixed!'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    'To automatically fix duplicates, run: python manage.py check_duplicate_users --fix'
                )
            )
