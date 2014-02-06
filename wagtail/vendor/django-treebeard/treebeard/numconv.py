"""Convert strings to numbers and numbers to strings.

Gustavo Picon
https://tabo.pe/projects/numconv/

"""


__version__ = '2.1.1'

# from april fool's rfc 1924
BASE85 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' \
         '!#$%&()*+-;<=>?@^_`{|}~'

# rfc4648 alphabets
BASE16 = BASE85[:16]
BASE32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
BASE32HEX = BASE85[:32]
BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
BASE64URL = BASE64[:62] + '-_'

# http://en.wikipedia.org/wiki/Base_62 useful for url shorteners
BASE62 = BASE85[:62]


class NumConv(object):
    """Class to create converter objects.

        :param radix: The base that will be used in the conversions.
           The default value is 10 for decimal conversions.
        :param alphabet: A string that will be used as a encoding alphabet.
           The length of the alphabet can be longer than the radix. In this
           case the alphabet will be internally truncated.

           The default value is :data:`numconv.BASE85`

        :raise TypeError: when *radix* isn't an integer
        :raise ValueError: when *radix* is invalid
        :raise ValueError: when *alphabet* has duplicated characters
    """

    def __init__(self, radix=10, alphabet=BASE85):
        """basic validation and cached_map storage"""
        if int(radix) != radix:
            raise TypeError('radix must be an integer')
        if not 2 <= radix <= len(alphabet):
            raise ValueError('radix must be >= 2 and <= %d' % (
                len(alphabet), ))
        self.radix = radix
        self.alphabet = alphabet
        self.cached_map = dict(zip(self.alphabet, range(len(self.alphabet))))
        if len(self.cached_map) != len(self.alphabet):
            raise ValueError("duplicate characters found in '%s'" % (
                self.alphabet, ))

    def int2str(self, num):
        """Converts an integer into a string.

        :param num: A numeric value to be converted to another base as a
                    string.

        :rtype: string

        :raise TypeError: when *num* isn't an integer
        :raise ValueError: when *num* isn't positive
        """
        if int(num) != num:
            raise TypeError('number must be an integer')
        if num < 0:
            raise ValueError('number must be positive')
        radix, alphabet = self.radix, self.alphabet
        if radix in (8, 10, 16) and \
                alphabet[:radix].lower() == BASE85[:radix].lower():
            return ({8: '%o', 10: '%d', 16: '%x'}[radix] % num).upper()
        ret = ''
        while True:
            ret = alphabet[num % radix] + ret
            if num < radix:
                break
            num //= radix
        return ret

    def str2int(self, num):
        """Converts a string into an integer.

        If possible, the built-in python conversion will be used for speed
        purposes.

        :param num: A string that will be converted to an integer.

        :rtype: integer

        :raise ValueError: when *num* is invalid
        """
        radix, alphabet = self.radix, self.alphabet
        if radix <= 36 and alphabet[:radix].lower() == BASE85[:radix].lower():
            return int(num, radix)
        ret = 0
        lalphabet = alphabet[:radix]
        for char in num:
            if char not in lalphabet:
                raise ValueError("invalid literal for radix2int() with radix "
                                 "%d: '%s'" % (radix, num))
            ret = ret * radix + self.cached_map[char]
        return ret


def int2str(num, radix=10, alphabet=BASE85):
    """helper function for quick base conversions from integers to strings"""
    return NumConv(radix, alphabet).int2str(num)


def str2int(num, radix=10, alphabet=BASE85):
    """helper function for quick base conversions from strings to integers"""
    return NumConv(radix, alphabet).str2int(num)
