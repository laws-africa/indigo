from allauth.account import adapter, app_settings


class ModifiedAccountAdapter(adapter.DefaultAccountAdapter):
    def populate_username(self, request, user):
        """
        Fills in a valid username, if required and missing.  If the
        username is already present it is assumed to be valid
        (unique).
        """
        from allauth.account.utils import user_username, user_email, user_field
        first_name = user_field(user, 'first_name')
        last_name = user_field(user, 'last_name')

        # pass it the full name as the first item in 'txts' instead
        user_name = first_name + last_name

        email = user_email(user)
        username = user_username(user)
        if app_settings.USER_MODEL_USERNAME_FIELD:
            user_username(
                user,
                username or self.generate_unique_username([
                    user_name,
                    first_name,
                    last_name,
                    email,
                    username,
                    'user']))
