# -*- coding: utf-8 -*-
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from datetime import date
from collections import OrderedDict
from molo.core.tests.base import MoloTestCaseMixin
from molo.core.models import Main, Languages, SiteLanguageRelation
from molo.profiles.admin import ProfileUserAdmin, download_as_csv
from molo.profiles.models import (
    UserProfile, SecurityQuestion, SecurityAnswer, SecurityQuestionIndexPage)
from molo.profiles.admin import MultiSiteUserResource


class ModelsTestCase(TestCase, MoloTestCaseMixin):
    def setUp(self):
        self.mk_main()
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='tester')
        self.main = Main.objects.all().first()
        self.language_setting = Languages.objects.create(
            site_id=self.main.get_site().pk)
        self.english = SiteLanguageRelation.objects.create(
            language_setting=self.language_setting,
            locale='en',
            is_active=True)
        self.mk_main2()

    def test_download_csv(self):
        profile = self.user.profile
        profile.alias = 'The Alias'
        profile.mobile_number = '+27784667723'
        profile.save()

        response = download_as_csv(ProfileUserAdmin(UserProfile, self.site),
                                   None,
                                   User.objects.all())
        date = str(self.user.date_joined.strftime("%Y-%m-%d %H:%M"))
        expected_output = ('Content-Type: text/csv\r\nContent-Disposition: '
                           'attachment;filename=export.csv\r\n\r\nusername,'
                           'email,first_name,last_name,is_staff,date_joined,'
                           'alias,mobile_number\r\ntester,tester@example.com,'
                           ',,False,' + date + ',The Alias,+27784667723\r\n')
        self.assertEquals(str(response), expected_output)

    def test_download_csv_with_an_alias_contains_ascii_code(self):
        profile = self.user.profile
        profile.alias = 'The Alias 😁'
        profile.mobile_number = '+27784667723'
        profile.save()

        response = download_as_csv(ProfileUserAdmin(UserProfile, self.site),
                                   None,
                                   User.objects.all())
        date = str(self.user.date_joined.strftime("%Y-%m-%d %H:%M"))
        expected_output = ('Content-Type: text/csv\r\nContent-Disposition: '
                           'attachment;filename=export.csv\r\n\r\nusername,'
                           'email,first_name,last_name,is_staff,date_joined,'
                           'alias,mobile_number\r\ntester,tester@example.com,'
                           ',,False,' + date + ',The Alias \xf0\x9f\x98\x81,'
                           '+27784667723\r\n')
        self.assertEquals(str(response), expected_output)

    def test_download_csv_with_an_username_contains_ascii_code(self):
        self.user.username = '사이네'
        self.user.save()

        response = download_as_csv(ProfileUserAdmin(UserProfile, self.site),
                                   None,
                                   User.objects.all())
        date = str(self.user.date_joined.strftime("%Y-%m-%d %H:%M"))
        expected_output = ('Content-Type: text/csv\r\nContent-Disposition: '
                           'attachment;filename=export.csv\r\n\r\nusername,'
                           'email,first_name,last_name,is_staff,date_joined,'
                           'alias,mobile_number\r\n\xec\x82\xac\xec\x9d\xb4'
                           '\xeb\x84\xa4,tester@example.com,'
                           ',,False,' + date + ',,\r\n')
        self.assertEquals(str(response), expected_output)

    def test_successful_login_for_migrated_users(self):
        user = User.objects.create_user(
            username='1_newuser',
            email='newuser@example.com',
            password='newuser')
        user.profile.migrated_username = 'newuser'
        user.profile.save()

        response = self.client.post('/profiles/login/?next=/', {
            'username': 'newuser',
            'password': 'newuser',
        })
        self.assertRedirects(response, '/')

        client = Client(HTTP_HOST=self.site2.hostname)

        response = client.post('/profiles/login/?next=/', {
            'username': 'newuser',
            'password': 'newuser',
        })
        self.assertContains(
            response,
            'Your username and password do not match. Please try again.')

    def test_successful_login_for_migrated_users_in_site_2(self):
        user = User.objects.create_user(
            username='2_newuser',
            email='newuser@example.com',
            password='newuser')
        user.profile.migrated_username = 'newuser'
        user.profile.site = self.site2
        user.profile.save()

        response = self.client.post('/profiles/login/?next=/', {
            'username': 'newuser',
            'password': 'newuser',
        })
        self.assertContains(
            response,
            'Your username and password do not match. Please try again.')

        client = Client(HTTP_HOST=self.site2.hostname)

        response = client.post('/profiles/login/?next=/', {
            'username': 'newuser',
            'password': 'newuser',
        })
        self.assertRedirects(response, '/')

    def test_security_question_dehydrate_method(self):
        user = User.objects.create_user(
            username='2_newuser',
            email='newuser@example.com',
            password='newuser')
        user.profile.migrated_username = 'newuser'
        user.profile.site = self.site2
        user.profile.save()

        self.security_index = SecurityQuestionIndexPage(
            title='Security Questions',
            slug='security_questions',
        )
        self.main.add_child(instance=self.security_index)
        self.security_index.save()
        self.question = SecurityQuestion(
            title="How old are you?",
            slug="how-old-are-you",
        )
        self.security_index.add_child(instance=self.question)
        self.question.save()

        # create answers for this user
        self.a1 = SecurityAnswer.objects.create(
            user=user.profile, question=self.question, answer="20"
        )
        resource = MultiSiteUserResource()
        result = resource.dehydrate_security_question_answers(user)

        # it should return a tuple of the question title and answer hash
        expected_result = [(self.question.title, self.a1.answer)]
        self.assertEquals(result, expected_result)

    def test_importing_does_not_override_existing_data(self):
        user = User.objects.create_user(
            username='2_newuser',
            email='newuser@example.com',
            password='newuser')
        user.profile.migrated_username = 'newuser'
        user.profile.site = self.site2
        user.profile.save()
        self.assertEquals(User.objects.count(), 2)
        data = OrderedDict(
            [('security_question_answers',
              []),
             ('username', user.username),
             ('first_name', ''),
             ('last_name', ''),
             ('migrated_username', user.profile.migrated_username),
             ('gender', ''),
             ('is_active', '1'),
             ('site', '1'),
             ('alias', ''),
             ('date_of_birth', ''),
             ('mobile_number', ''),
             ('password', user.password),
             ('email', user.email),
             ('date_joined', user.date_joined)
             ]
        )
        resource = MultiSiteUserResource()
        result = resource.import_row(row=data, instance_loader=None)
        self.assertEquals(result.IMPORT_TYPE_SKIP, u'skip')
        self.assertEquals(User.objects.count(), 2)

    def test_import_creates_security_questions_and_creates_answers(self):
        self.assertEquals(SecurityQuestion.objects.count(), 0)
        self.assertEquals(SecurityAnswer.objects.count(), 0)
        resource = MultiSiteUserResource()
        hash_1 = ('pbkdf2_sha256$24000$WwoRrb5eO3SG$fghoNMPmIGhakF/L'
                  '3uulZ37Ly9LNvR0UpFuhvjf7zQM=')
        hash_2 = ('pbkdf2_sha256$24000$bfuPwkO3ZBtY$rRtO3H'
                  'BV6wlwsaGsa+04PDn+0maZxBgbXJl6PwQIoVQ=')
        hash_3 = ('pbkdf2_sha256$24000$DmvPwpVz13Qh$VvW/dRDHmRE7Vk45'
                  'Ax4H6RwFje4yVt1ofZwbLaG7a80=')
        hash_4 = ('pbkdf2_sha256$24000$wOf9Zt3RBDlS$v61vMnq7pDJEz3'
                  'vV/UP8cBL7PFCCCcDFTCH0FS2XVq0=')

        data = OrderedDict(
            [('security_question_answers',
              [
                  ['Who am I?', hash_1],
                  ['What is my name?', hash_2],
                  ['Say Whaaaat?', hash_3]
              ]),
             ('username', '3_3_codieroelf2'),
             ('first_name', ''),
             ('last_name', ''),
             ('migrated_username', '3_codieroelf2'),
             ('gender', ''),
             ('is_active', '1'),
             ('site', '1'),
             ('alias', ''),
             ('date_of_birth', ''),
             ('mobile_number', ''),
             ('password', hash_4),
             ('email', ''),
             ('date_joined', '2017-09-07 08:43:18')
             ]
        )

        resource.import_obj(obj=User(), data=data, dry_run=True)
        self.assertEquals(SecurityQuestion.objects.count(), 3)
        self.assertEquals(SecurityAnswer.objects.count(), 3)
        questions = SecurityQuestion.objects.all()
        for question in questions:
            self.assertTrue(SecurityAnswer.objects.filter(
                question=question).exists())


class TestFrontendUsersAdminView(TestCase, MoloTestCaseMixin):
    def setUp(self):
        self.mk_main()
        self.main = Main.objects.all().first()
        self.language_setting = Languages.objects.create(
            site_id=self.main.get_site().pk)
        self.english = SiteLanguageRelation.objects.create(
            language_setting=self.language_setting,
            locale='en',
            is_active=True)
        self.client.post(reverse('molo.profiles:user_register'), {
            'username': 'testing1',
            'password': '1234',
            'terms_and_conditions': True

        })
        self.user = User.objects.get(username='testing1')

        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='admin@example.com',
            password='0000',
            is_staff=True)

        self.client = Client()
        self.client.login(username='superuser', password='0000')

    def test_staff_users_are_not_shown(self):
        response = self.client.get(
            '/admin/auth/user/?usertype=frontend'
        )
        self.assertContains(response, self.user.username)
        self.assertNotContains(response, self.superuser.email)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_export_csv_redirects(self):
        profile = self.user.profile
        profile.alias = 'The Alias'
        profile.date_of_birth = date(1985, 1, 1)
        profile.mobile_number = '+27784667723'
        profile.save()
        response = self.client.post('/admin/auth/user/')

        self.assertEquals(response.status_code, 302)


class TestAdminUserView(TestCase, MoloTestCaseMixin):
    def setUp(self):
        self.mk_main()
        self.main = Main.objects.all().first()
        self.language_setting = Languages.objects.create(
            site_id=self.main.get_site().pk)
        self.english = SiteLanguageRelation.objects.create(
            language_setting=self.language_setting,
            locale='en',
            is_active=True)
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='0000',
            is_staff=False)

        self.superuser = User.objects.create_superuser(
            username='superuser',
            email='admin@example.com',
            password='0000',
            is_staff=True)

        self.client = Client()
        self.client.login(username='superuser', password='0000')

    def test_exclude_all_end_users(self):
        response = self.client.get(
            '/admin/auth/user/?usertype=admin'
        )
        self.assertContains(response, self.superuser.username)
        self.assertNotContains(response, self.user.username)
