# -*- coding: utf-8 -*-
import datetime
import uuid
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
try:
    from django.utils import lorem_ipsum
except ImportError:
    # Support Django < 1.8
    from django.contrib.webdesign import lorem_ipsum
import os
import random
import re
import string
import sys
from decimal import Decimal


if sys.version_info[0] < 3:
    str_ = unicode
else:
    str_ = str


# backporting os.path.relpath, only availabe in python >= 2.6
try:
    relpath = os.path.relpath
except AttributeError:
    def relpath(path, start=os.curdir):
        """Return a relative version of a path"""

        if not path:
            raise ValueError("no path specified")

        start_list = os.path.abspath(start).split(os.path.sep)
        path_list = os.path.abspath(path).split(os.path.sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(os.path.commonprefix([start_list, path_list]))

        rel_list = [os.path.pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return os.curdir
        return os.path.join(*rel_list)


class Generator(object):
    coerce_type = staticmethod(lambda x: x)
    empty_value = None
    empty_p = 0

    def __init__(self, empty_p=None, coerce=None):
        if empty_p is not None:
            self.empty_p = empty_p
        if coerce:
            self.coerce_type = coerce

    def coerce(self, value):
        return self.coerce_type(value)

    def generate(self):
        raise NotImplementedError

    def get_value(self):
        if random.random() < self.empty_p:
            return self.empty_value
        value = self.generate()
        return self.coerce(value)

    def __call__(self):
        return self.get_value()


class StaticGenerator(Generator):
    def __init__(self, value, *args, **kwargs):
        self.value = value
        super(StaticGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return self.value


class CallableGenerator(Generator):
    def __init__(self, value, args=None, kwargs=None, *xargs, **xkwargs):
        self.value = value
        self.args = args or ()
        self.kwargs = kwargs or {}
        super(CallableGenerator, self).__init__(*xargs, **xkwargs)

    def generate(self):
        return self.value(*self.args, **self.kwargs)


class NoneGenerator(Generator):
    def generate(self):
        return self.empty_value


class StringGenerator(Generator):
    coerce_type = str_
    singleline_chars = string.ascii_letters + u' '
    multiline_chars = singleline_chars + u'\n'

    def __init__(self, chars=None, multiline=False, min_length=1, max_length=1000, *args, **kwargs):
        assert min_length >= 0
        assert max_length >= 0
        self.min_length = min_length
        self.max_length = max_length
        if chars is None:
            if multiline:
                self.chars = self.multiline_chars
            else:
                self.chars = self.singleline_chars
        else:
            self.chars = chars
        super(StringGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        length = random.randint(self.min_length, self.max_length)
        value = u''
        for x in range(length):
            value += random.choice(self.chars)
        return value


class SlugGenerator(StringGenerator):
    def __init__(self, chars=None, *args, **kwargs):
        if chars is None:
            chars = string.ascii_lowercase + string.digits + '-'
        super(SlugGenerator, self).__init__(chars, multiline=False, *args, **kwargs)


class LoremGenerator(Generator):
    coerce_type = str_
    common = True
    count = 3
    method = 'b'

    def __init__(self, count=None, method=None, common=None, max_length=None, *args, **kwargs):
        if count is not None:
            self.count = count
        if method is not None:
            self.method = method
        if common is not None:
            self.common = common
        self.max_length = max_length
        super(LoremGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        if self.method == 'w':
            lorem = lorem_ipsum.words(self.count, common=self.common)
        elif self.method == 's':
            lorem = u' '.join([
                lorem_ipsum.sentence()
                for i in range(self.count)])
        else:
            paras = lorem_ipsum.paragraphs(self.count, common=self.common)
            if self.method == 'p':
                paras = ['<p>%s</p>' % p for p in paras]
            lorem = u'\n\n'.join(paras)
        if self.max_length:
            length = random.randint(round(int(self.max_length) / 10),
                                    self.max_length)
            lorem = lorem[:max(1, length)]
        return lorem.strip()


class LoremSentenceGenerator(LoremGenerator):
    method = 's'


class LoremHTMLGenerator(LoremGenerator):
    method = 'p'


class LoremWordGenerator(LoremGenerator):
    count = 7
    method = 'w'


class IntegerGenerator(Generator):
    coerce_type = int
    min_value = - 10 ** 5
    max_value = 10 ** 5

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value
        super(IntegerGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        value = random.randint(self.min_value, self.max_value)
        return value


class SmallIntegerGenerator(IntegerGenerator):
    min_value = -2 ** 7
    max_value = 2 ** 7 - 1


class PositiveIntegerGenerator(IntegerGenerator):
    min_value = 0


class PositiveSmallIntegerGenerator(SmallIntegerGenerator):
    min_value = 0


class FloatGenerator(IntegerGenerator):
    coerce_type = float
    decimal_digits = 1

    def __init__(self, decimal_digits=None, *args, **kwargs):
        if decimal_digits is not None:
            self.decimal_digits = decimal_digits
        super(FloatGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        value = super(FloatGenerator, self).generate()
        value = float(value)
        if self.decimal_digits:
            digits = random.randint(1, 10 ^ self.decimal_digits) - 1
            digits = float(digits)
            value = value + digits / (10 ^ self.decimal_digits)
        return value


class ChoicesGenerator(Generator):
    def __init__(self, choices=(), values=(), *args, **kwargs):
        assert len(choices) or len(values)
        self.choices = list(choices)
        if not values:
            self.values = [k for k, v in self.choices]
        else:
            self.values = list(values)
        super(ChoicesGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return random.choice(self.values)


class BooleanGenerator(ChoicesGenerator):
    def __init__(self, none=False, *args, **kwargs):
        values = (True, False)
        if none:
            values = values + (None,)
        super(BooleanGenerator, self).__init__(values=values, *args, **kwargs)


class NullBooleanGenerator(BooleanGenerator):
    def __init__(self, none=True, *args, **kwargs):
        super(NullBooleanGenerator, self).__init__(none=none, *args, **kwargs)


class DateTimeGenerator(Generator):
    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        from django.utils import timezone
        if min_date is not None:
            self.min_date = min_date
        else:
            self.min_date = timezone.now() - datetime.timedelta(365 * 5)
        if max_date is not None:
            self.max_date = max_date
        else:
            self.max_date = timezone.now() + datetime.timedelta(365 * 1)
        assert self.min_date < self.max_date
        super(DateTimeGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        seconds = random.randint(0, diff.days * 3600 * 24 + diff.seconds)
        return self.min_date + datetime.timedelta(seconds=seconds)


class DateGenerator(Generator):
    min_date = datetime.date.today() - datetime.timedelta(365 * 5)
    max_date = datetime.date.today() + datetime.timedelta(365 * 1)

    def __init__(self, min_date=None, max_date=None, *args, **kwargs):
        if min_date is not None:
            self.min_date = min_date
        if max_date is not None:
            self.max_date = max_date
        assert self.min_date < self.max_date
        super(DateGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        diff = self.max_date - self.min_date
        days = random.randint(0, diff.days)
        date = self.min_date + datetime.timedelta(days=days)
        return date
        return datetime.date(date.year, date.month, date.day)


class DecimalGenerator(Generator):
    coerce_type = Decimal

    max_digits = 24
    decimal_places = 10

    def __init__(self, max_digits=None, decimal_places=None, *args, **kwargs):
        if max_digits is not None:
            self.max_digits = max_digits
        if decimal_places is not None:
            self.decimal_places = decimal_places
        super(DecimalGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        maxint = 10 ** self.max_digits - 1
        value = (
            Decimal(random.randint(-maxint, maxint)) /
            10 ** self.decimal_places)
        return value


class PositiveDecimalGenerator(DecimalGenerator):
    def generate(self):
        maxint = 10 ** self.max_digits - 1
        value = (
            Decimal(random.randint(0, maxint)) /
            10 ** self.decimal_places)
        return value


class FirstNameGenerator(Generator):
    """ Generates a first name, either male or female """

    male = [
        'Abraham', 'Adam', 'Anthony', 'Brian', 'Bill', 'Ben', 'Calvin',
        'David', 'Daniel', 'George', 'Henry', 'Isaac', 'Ian', 'Jonathan',
        'Jeremy', 'Jacob', 'John', 'Jerry', 'Joseph', 'James', 'Larry',
        'Michael', 'Mark', 'Paul', 'Peter', 'Phillip', 'Stephen', 'Tony',
        'Titus', 'Trevor', 'Timothy', 'Victor', 'Vincent', 'Winston', 'Walt']
    female = [
        'Abbie', 'Anna', 'Alice', 'Beth', 'Carrie', 'Christina', 'Danielle',
        'Emma', 'Emily', 'Esther', 'Felicia', 'Grace', 'Gloria', 'Helen',
        'Irene', 'Joanne', 'Joyce', 'Jessica', 'Kathy', 'Katie', 'Kelly',
        'Linda', 'Lydia', 'Mandy', 'Mary', 'Olivia', 'Priscilla',
        'Rebecca', 'Rachel', 'Susan', 'Sarah', 'Stacey', 'Vivian']

    def __init__(self, gender=None):
        self.gender = gender
        self.all = self.male + self.female

    def generate(self):
        if self.gender == 'm':
            return random.choice(self.male)
        elif self.gender == 'f':
            return random.choice(self.female)
        else:
            return random.choice(self.all)


class LastNameGenerator(Generator):
    """ Generates a last name """

    surname = [
        'Smith', 'Walker', 'Conroy', 'Stevens', 'Jones', 'Armstrong',
        'Johnson', 'White', 'Stone', 'Strong', 'Olson', 'Lee', 'Forrest',
        'Baker', 'Portman', 'Davis', 'Clark', 'Brown', 'Roberts', 'Ellis',
        'Jackson', 'Marshall', 'Wang', 'Chen', 'Chou', 'Tang', 'Huang', 'Liu',
        'Shih', 'Su', 'Song', 'Yang', 'Chan', 'Tsai', 'Wong', 'Hsu', 'Cheng',
        'Chang', 'Wu', 'Lin', 'Yu', 'Yao', 'Kang', 'Park', 'Kim', 'Choi',
        'Ahn', 'Mujuni']

    def generate(self):
        return random.choice(self.surname)


class EmailGenerator(StringGenerator):
    chars = string.ascii_lowercase

    def __init__(self, chars=None, max_length=30, tlds=None, static_domain=None, *args, **kwargs):
        assert max_length >= 6
        if chars is not None:
            self.chars = chars
        self.tlds = tlds
        self.static_domain = static_domain
        super(EmailGenerator, self).__init__(self.chars, max_length=max_length, *args, **kwargs)

    def generate(self):
        maxl = self.max_length - 2

        if self.static_domain is None:
            if self.tlds:
                tld = random.choice(self.tlds)
            elif maxl > 4:
                tld = StringGenerator(self.chars, min_length=3, max_length=3).generate()
            maxl -= len(tld)
            assert maxl >= 2
        else:
            maxl -= len(self.static_domain)

        name = StringGenerator(self.chars, min_length=1, max_length=maxl-1).generate()
        maxl -= len(name)

        if self.static_domain is None:
            domain = StringGenerator(self.chars, min_length=1, max_length=maxl).generate()
            return '%s@%s.%s' % (name, domain, tld)
        else:
            return '%s@%s' % (name, self.static_domain)


class URLGenerator(StringGenerator):
    chars = string.ascii_lowercase
    protocol = 'http'
    tlds = ()

    def __init__(self, chars=None, max_length=30, protocol=None, tlds=None,
        *args, **kwargs):
        if chars is not None:
            self.chars = chars
        if protocol is not None:
            self.protocol = protocol
        if tlds is not None:
            self.tlds = tlds
        assert max_length > (
            len(self.protocol) + len('://') +
            1 + len('.') +
            max([2] + [len(tld) for tld in self.tlds if tld]))
        super(URLGenerator, self).__init__(
            chars=self.chars, max_length=max_length, *args, **kwargs)

    def generate(self):
        maxl = self.max_length - len(self.protocol) - 4 # len(://) + len(.)
        if self.tlds:
            tld = random.choice(self.tlds)
            maxl -= len(tld)
        else:
            tld_max_length = 3 if maxl >= 5 else 2
            tld = StringGenerator(self.chars,
                min_length=2, max_length=tld_max_length).generate()
            maxl -= len(tld)
        domain = StringGenerator(chars=self.chars, max_length=maxl).generate()
        return u'%s://%s.%s' % (self.protocol, domain, tld)


class IPAddressGenerator(Generator):
    coerce_type = str_

    def generate(self):
        return '.'.join([str_(part) for part in [
            IntegerGenerator(min_value=1, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=0, max_value=254).generate(),
            IntegerGenerator(min_value=1, max_value=254).generate(),
        ]])


class TimeGenerator(Generator):
    coerce_type = str_

    def generate(self):
        return u'%02d:%02d:%02d' % (
            random.randint(0,23),
            random.randint(0,59),
            random.randint(0,59),
        )


class FilePathGenerator(Generator):
    coerce_type = str_

    def __init__(self, path, match=None, recursive=False, max_length=None, *args, **kwargs):
        self.path = path
        self.match = match
        self.recursive = recursive
        self.max_length = max_length
        super(FilePathGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        filenames = []
        if self.match:
            match_re = re.compile(self.match)
        if self.recursive:
            for root, dirs, files in os.walk(self.path):
                for f in files:
                    if self.match is None or self.match_re.search(f):
                        f = os.path.join(root, f)
                        filenames.append(f)
        else:
            try:
                for f in os.listdir(self.path):
                    full_file = os.path.join(self.path, f)
                    if os.path.isfile(full_file) and \
                        (self.match is None or match_re.search(f)):
                        filenames.append(full_file)
            except OSError:
                pass
        if self.max_length:
            filenames = [fn for fn in filenames if len(fn) <= self.max_length]
        return random.choice(filenames)


class MediaFilePathGenerator(FilePathGenerator):
    '''
    Generates a valid filename of an existing file from a subdirectory of
    ``settings.MEDIA_ROOT``. The returned filename is relative to
    ``MEDIA_ROOT``.
    '''
    def __init__(self, path='', *args, **kwargs):
        from django.conf import settings
        path = os.path.join(settings.MEDIA_ROOT, path)
        super(MediaFilePathGenerator, self).__init__(path, *args, **kwargs)

    def generate(self):
        from django.conf import settings
        filename = super(MediaFilePathGenerator, self).generate()
        filename = relpath(filename, settings.MEDIA_ROOT)
        return filename


class InstanceGenerator(Generator):
    '''
    Naive support for ``limit_choices_to``. It assignes specified value to
    field for dict items that have one of the following form::

        fieldname: value
        fieldname__exact: value
        fieldname__iexact: value
    '''
    def __init__(self, autofixture, limit_choices_to=None, *args, **kwargs):
        self.autofixture = autofixture
        limit_choices_to = limit_choices_to or {}
        for lookup, value in limit_choices_to.items():
            bits = lookup.split('__')
            if len(bits) == 1 or \
                len(bits) == 2 and bits[1] in ('exact', 'iexact'):
                self.autofixture.add_field_value(bits[0], StaticGenerator(value))
        super(InstanceGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        return self.autofixture.create()[0]


class MultipleInstanceGenerator(InstanceGenerator):
    empty_value = []

    def __init__(self, *args, **kwargs):
        self.min_count = kwargs.pop('min_count', 1)
        self.max_count = kwargs.pop('max_count', 10)
        super(MultipleInstanceGenerator, self).__init__(*args, **kwargs)

    def generate(self):
        instances = []
        for i in range(random.randint(self.min_count, self.max_count)):
            instances.append(
                super(MultipleInstanceGenerator, self).generate())
        return instances


class InstanceSelector(Generator):
    '''
    Select one or more instances from a queryset.
    '''
    empty_value = []

    def __init__(self, queryset, min_count=None, max_count=None, fallback=None,
        limit_choices_to=None, *args, **kwargs):
        from django.db.models.query import QuerySet
        if not isinstance(queryset, QuerySet):
            queryset = queryset._default_manager.all()
        limit_choices_to = limit_choices_to or {}
        self.queryset = queryset.filter(**limit_choices_to)
        self.fallback = fallback
        self.min_count = min_count
        self.max_count = max_count
        super(InstanceSelector, self).__init__(*args, **kwargs)

    def generate(self):
        if self.max_count is None:
            try:
                return self.queryset.order_by('?')[0]
            except IndexError:
                return self.fallback
        else:
            min_count = self.min_count or 0
            count = random.randint(min_count, self.max_count)
            return self.queryset.order_by('?')[:count]

class WeightedGenerator(Generator):
    """
    Takes a list of generator objects and integer weights, of the following form:
    [(generator, weight), (generator, weight),...]
    and returns a value from a generator chosen randomly by weight.
    """

    def __init__(self, choices):
        self.choices = choices

    def weighted_choice(self, choices):
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        upto = 0
        for c, w in choices:
          if upto + w > r:
             return c
          upto += w

    def generate(self):
        return self.weighted_choice(self.choices).generate()

class ImageGenerator(Generator):
    '''
    Generates a valid palceholder image and saves it to the ``settings.MEDIA_ROOT``
    The returned filename is relative to ``MEDIA_ROOT``.
    '''

    default_sizes = (
        (100,100),
        (200,300),
        (400,600),
    )

    def __init__(self, width=None, height=None, sizes=None,
                 path='_autofixture', storage=None, *args, **kwargs):
        self.width = width
        self.height = height
        self.sizes = list(sizes or self.default_sizes)
        if self.width and self.height:
            self.sizes.append((width, height))
        self.path = path
        self.storage = storage or default_storage
        super(ImageGenerator, self).__init__(*args, **kwargs)

    def generate_file_path(self, width, height, suffix=None):
        suffix = suffix if suffix is not None else ''
        filename ='{width}x{height}{suffix}.png'.format(
            width=width, height=height, suffix=suffix)
        return os.path.join(self.path, filename)

    def generate(self):
        from .placeholder import get_placeholder_image

        width, height = random.choice(self.sizes)

        # Ensure that _autofixture folder exists.
        i = 0
        path = self.generate_file_path(width, height)

        while self.storage.exists(path):
            i += 1
            path = self.generate_file_path(width, height, '_{0}'.format(i))

        return self.storage.save(
            path,
            ContentFile(get_placeholder_image(width, height))
        )


class UUIDGenerator(Generator):
    '''
    Generates random uuid4.
    '''

    def generate(self):
        return uuid.uuid4()
