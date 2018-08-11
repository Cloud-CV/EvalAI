#!/usr/bin/env python
# 2014 - Bibek Kafle & Roland Shoemaker
# Port of @jgm's JavaScript stmd.js implementation of the CommonMark spec

# Basic usage:
#
# import CommonMark
# parser = CommonMark.DocParser()
# renderer = CommonMark.HtmlRenderer()
# print(renderer.render(parser.parse('Hello *world*')))
import re, sys, argparse, json

# if python3 use html.parser and urllib.parse, else use HTMLParser and urllib
if sys.version_info >= (3, 0):
    import urllib.parse
    if sys.version_info >= (3, 4):
        import html.parser
        HTMLunescape = html.parser.HTMLParser().unescape
    else:
        from .entitytrans import _unescape
        HTMLunescape = _unescape
    HTMLquote = urllib.parse.quote
    HTMLunquote = urllib.parse.unquote
    URLparse = urllib.parse.urlparse
else:
    import urllib, urlparse
    import entitytrans
    HTMLunescape = entitytrans._unescape
    HTMLquote = urllib.quote
    HTMLunquote = urllib.unquote
    URLparse = urlparse.urlparse

# Some of the regexps used in inline parser :<

ESCAPABLE = '[!"#$%&\'()*+,./:;<=>?@[\\\\\\]^_`{|}~-]'
ESCAPED_CHAR = '\\\\' + ESCAPABLE
IN_DOUBLE_QUOTES = '"(' + ESCAPED_CHAR + '|[^"\\x00])*"'
IN_SINGLE_QUOTES = '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\''
IN_PARENS = '\\((' + ESCAPED_CHAR + '|[^)\\x00])*\\)'
REG_CHAR = '[^\\\\()\\x00-\\x20]'
IN_PARENS_NOSP = '\\((' + REG_CHAR + '|' + ESCAPED_CHAR + ')*\\)'
TAGNAME = '[A-Za-z][A-Za-z0-9]*'
BLOCKTAGNAME = '(?:article|header|aside|hgroup|iframe|blockquote|hr|body|li|map|button|object|canvas|ol|caption|output|col|p|colgroup|pre|dd|progress|div|section|dl|table|td|dt|tbody|embed|textarea|fieldset|tfoot|figcaption|th|figure|thead|footer|footer|tr|form|ul|h1|h2|h3|h4|h5|h6|video|script|style)'
ATTRIBUTENAME = '[a-zA-Z_:][a-zA-Z0-9:._-]*'
UNQUOTEDVALUE = "[^\"'=<>`\\x00-\\x20]+"
SINGLEQUOTEDVALUE = "'[^']*'"
DOUBLEQUOTEDVALUE = '"[^"]*"'
ATTRIBUTEVALUE = "(?:" + UNQUOTEDVALUE + "|" + \
    SINGLEQUOTEDVALUE + "|" + DOUBLEQUOTEDVALUE + ")"
ATTRIBUTEVALUESPEC = "(?:" + "\\s*=" + "\\s*" + ATTRIBUTEVALUE + ")"
ATTRIBUTE = "(?:" + "\\s+" + ATTRIBUTENAME + ATTRIBUTEVALUESPEC + "?)"
OPENTAG = "<" + TAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSETAG = "</" + TAGNAME + "\\s*[>]"
OPENBLOCKTAG = "<" + BLOCKTAGNAME + ATTRIBUTE + "*" + "\\s*/?>"
CLOSEBLOCKTAG = "</" + BLOCKTAGNAME + "\\s*[>]"
HTMLCOMMENT = "<!--([^-]+|[-][^-]+)*-->"
PROCESSINGINSTRUCTION = "[<][?].*?[?][>]"
DECLARATION = "<![A-Z]+" + "\\s+[^>]*>"
CDATA = "<!\\[CDATA\\[([^\\]]+|\\][^\\]]|\\]\\][^>])*\\]\\]>"
HTMLTAG = "(?:" + OPENTAG + "|" + CLOSETAG + "|" + HTMLCOMMENT + \
    "|" + PROCESSINGINSTRUCTION + "|" + DECLARATION + "|" + CDATA + ")"
HTMLBLOCKOPEN = "<(?:" + BLOCKTAGNAME + \
    "[\\s/>]" + "|" + "/" + \
    BLOCKTAGNAME + "[\\s>]" + "|" + "[?!])"

reHtmlTag = re.compile('^' + HTMLTAG, re.IGNORECASE)
reHtmlBlockOpen = re.compile('^' + HTMLBLOCKOPEN, re.IGNORECASE)
reLinkTitle = re.compile(
    '^(?:"(' + ESCAPED_CHAR + '|[^"\\x00])*"' + '|' + '\'(' + ESCAPED_CHAR + '|[^\'\\x00])*\'' + '|' + '\\((' + ESCAPED_CHAR + '|[^)\\x00])*\\))')
reLinkDestinationBraces = re.compile(
    '^(?:[<](?:[^<>\\n\\\\\\x00]' + '|' + ESCAPED_CHAR + '|' + '\\\\)*[>])')
reLinkDestination = re.compile(
    '^(?:' + REG_CHAR + '+|' + ESCAPED_CHAR + '|' + IN_PARENS_NOSP + ')*')
reEscapable = re.compile(ESCAPABLE)
reAllEscapedChar = '\\\\(' + ESCAPABLE + ')'
reEscapedChar = re.compile('^\\\\(' + ESCAPABLE + ')')
reAllTab = re.compile("\t")
reHrule = re.compile(r"^(?:(?:\* *){3,}|(?:_ *){3,}|(?:- *){3,}) *$")

# Matches a character with a special meaning in markdown,
# or a string of non-special characters.
reMain = r"^(?:[\n`\[\]\\!<&*_]|[^\n`\[\]\\!<&*_]+)"

# Utility functions

def ASTtoJSON(block):
    """ Output AST in JSON form, this is destructive of block."""
    def prepare(block):
        """ Strips circular 'parent' references and trims empty block elements."""
        if block.parent:
            block.parent = None
        if not block.__dict__['isOpen'] is None:
            block.__dict__['open'] = block.isOpen
            del(block.isOpen)
        # trim empty elements...
        for attr in dir(block):
            if not callable(attr) and not attr.startswith("__") and not attr == "makeBlock":
                if block.__dict__[attr] in ["", [], None, {}]:
                    del(block.__dict__[attr])
        if 'children' in block.__dict__ and len(block.children) > 0:
            for i, child in enumerate(block.children):
                block.children[i] = prepare(child)
        if 'inline_content' in block.__dict__ and len(block.inline_content) > 0:
            for i, child in enumerate(block.inline_content):
                block.inline_content[i] = prepare(child)
        if 'label' in block.__dict__ and len(block.label) > 0:
            for i, child in enumerate(block.label):
                block.label[i] = prepare(child)
        if 'c' in block.__dict__  and type(block.c) is list and len(block.c) > 0:
            for i, child in enumerate(block.c):
                block.c[i] = prepare(child)
        return block
    return json.dumps(prepare(block), default=lambda o: o.__dict__) # sort_keys=True) # indent=4)

def dumpAST(obj, ind=0):
    """ Print out a block/entire AST."""
    indChar = ("\t" * ind) + "-> " if ind else ""
    print(indChar + "[" + obj.t + "]")
    if not obj.title == "":
        print("\t" + indChar + "Title: " + obj.title)
    if not obj.info == "":
        print("\t" + indChar + "Info: " + obj.info)
    if not obj.destination == "":
        print("\t" + indChar + "Destination: " + obj.destination)
    if obj.isOpen:
        print("\t" + indChar + "Open: " + str(obj.isOpen))
    if obj.last_line_blank:
        print(
            "\t" + indChar + "Last line blank: " + str(obj.last_line_blank))
    if obj.start_line:
        print("\t" + indChar + "Start line: " + str(obj.start_line))
    if obj.start_column:
        print("\t" + indChar + "Start Column: " + str(obj.start_column))
    if obj.end_line:
        print("\t" + indChar + "End line: " + str(obj.end_line))
    if not obj.string_content == "":
        print("\t" + indChar + "String content: " + obj.string_content)
    if not obj.info == "":
        print("\t" + indChar + "Info: " + obj.info)
    if len(obj.strings) > 0:
        print("\t" + indChar + "Strings: ['" + "', '".join(obj.strings) + "'']")
    if obj.c:
        if type(obj.c) is list:
            print("\t" + indChar + "c:")
            for b in obj.c:
                dumpAST(b, ind + 2)
        else:
            print("\t" + indChar + "c: "+obj.c)
    if obj.label:
        print("\t" + indChar + "Label:")
        for b in obj.label:
            dumpAST(b, ind + 2)
    if hasattr(obj.list_data, "type"):
        print("\t" + indChar + "List Data: ")
        print("\t\t" + indChar + "[type] = " + obj.list_data['type'])
        if hasattr(obj.list_data, "bullet_char"):
            print(
                "\t\t" + indChar + "[bullet_char] = " + obj.list_data['bullet_char'])
        if hasattr(obj.list_data, "start"):
            print("\t\t" + indChar + "[start] = " + obj.list_data['start'])
        if hasattr(obj.list_data, "delimiter"):
            print(
                "\t\t" + indChar + "[delimiter] = " + obj.list_data['delimiter'])
        if hasattr(obj.list_data, "padding"):
            print(
                "\t\t" + indChar + "[padding] = " + obj.list_data['padding'])
        if hasattr(obj.list_data, "marker_offset"):
            print(
                "\t\t" + indChar + "[marker_offset] = " + obj.list_data['marker_offset'])
    if len(obj.inline_content) > 0:
        print("\t" + indChar + "Inline content:")
        for b in obj.inline_content:
            dumpAST(b, ind + 2)
    if len(obj.children) > 0:
        print("\t" + indChar + "Children:")
        for b in obj.children:
            dumpAST(b, ind + 2)

def unescape(s):
    """ Replace backslash escapes with literal characters."""
    return re.sub(reAllEscapedChar, r"\g<1>", s)


def isBlank(s):
    """ Returns True if string contains only space characters."""
    return bool(re.compile("^\s*$").match(s))


def normalizeReference(s):
    """ Normalize reference label: collapse internal whitespace to
    single space, remove leading/trailing whitespace, case fold."""
    return re.sub(r'\s+', ' ', s.strip()).upper()


def matchAt(pattern, s, offset):
    """ Attempt to match a regex in string s at offset offset.
    Return index of match or None."""
    matched = re.search(pattern, s[offset:])
    if matched:
        return offset + s[offset:].index(matched.group(0))
    else:
        return None


def detabLine(text):
    """ Convert tabs to spaces on each line using a 4-space tab stop."""
    if re.match('\t', text) and text.index('\t') == -1:
        return text
    else:
        def tabber(m):
            result = "    "[(m.end() - 1 - tabber.lastStop) % 4:]
            tabber.lastStop = m.end()
            return result
        tabber.lastStop = 0
        text = re.sub("\t", tabber, text)
        return text


class Block(object):

    @staticmethod
    def makeBlock(tag, start_line, start_column):
        return Block(t=tag, start_line=start_line, start_column=start_column)

    def __init__(self, t="", c="", destination="", label="", start_line="", start_column="", title=""):
        self.t = t
        self.c = c
        self.destination = destination
        self.label = label
        self.isOpen = True
        self.last_line_blank = False
        self.start_line = start_line
        self.start_column = start_column
        self.end_line = start_line
        self.children = []
        self.parent = None
        self.string_content = ""
        self.strings = []
        self.inline_content = []
        self.list_data = {}
        self.title = title
        self.info = ""
        self.tight = bool()

class InlineParser(object):

    """  INLINE PARSER

     These are methods of an InlineParser class, defined below.
     An InlineParser keeps track of a subject (a string to be
     parsed) and a position in that subject.

     If re matches at current position in the subject, advance
     position in subject and return the match; otherwise return null."""

    def __init__(self):
        self.subject = ""
        self.label_nest_level = 0
        self.pos = 0
        self.refmap = {}

    def match(self, regexString, reCompileFlags=0):
        """ If re matches at current position in the subject, advance
        position in subject and return the match; otherwise return null."""
        match = re.search(
            regexString, self.subject[self.pos:], flags=reCompileFlags)
        if match:
            self.pos += match.end(0)
            return match.group()
        else:
            return None

    def peek(self):
        """ Returns the character at the current subject position, or null if
        there are no more characters."""
        try:
            return self.subject[self.pos]
        except IndexError:
            return None

    def spnl(self):
        """ Parse zero or more space characters, including at most one newline."""
        self.match(r"^ *(?:\n *)?")
        return 1

    # All of the parsers below try to match something at the current position
    # in the subject.  If they succeed in matching anything, they
    # push an inline element onto the 'inlines' list.  They return the
    # number of characters parsed (possibly 0).

    def parseBackticks(self, inlines):
        """ Attempt to parse backticks, adding either a backtick code span or a
        literal sequence of backticks to the 'inlines' list."""
        startpos = self.pos
        ticks = self.match(r"^`+")
        if not ticks:
            return 0
        afterOpenTicks = self.pos
        foundCode = False
        match = self.match(r"`+", re.MULTILINE)
        while (not foundCode) and (not match is None):
            if (match == ticks):
                c = self.subject[afterOpenTicks:(self.pos - len(ticks))]
                c = re.sub(r"[ \n]+", ' ', c)
                c = c.strip()
                inlines.append(Block(t="Code", c=c))
                return (self.pos - startpos)
            match = self.match(r"`+", re.MULTILINE)
        inlines.append(Block(t="Str", c=ticks))
        self.pos = afterOpenTicks
        return (self.pos - startpos)

    def parseEscaped(self, inlines):
        """ Parse a backslash-escaped special character, adding either the escaped
        character, a hard line break (if the backslash is followed by a newline),
        or a literal backslash to the 'inlines' list."""
        subj = self.subject
        pos = self.pos
        if (subj[pos] == "\\"):
            if len(subj) > pos + 1 and (subj[pos + 1] == "\n"):
                inlines.append(Block(t="Hardbreak"))
                self.pos += 2
                return 2
            elif (reEscapable.search(subj[pos + 1:pos + 2])):
                inlines.append(Block(t="Str", c=subj[pos + 1:pos + 2]))
                self.pos += 2
                return 2
            else:
                self.pos += 1
                inlines.append(Block(t="Str", c="\\"))
                return 1
        else:
            return 0

    def parseAutoLink(self, inlines):
        """ Attempt to parse an autolink (URL or email in pointy brackets)."""
        m = self.match(
            "^<([a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*)>")
        m2 = self.match(
            "^<(?:coap|doi|javascript|aaa|aaas|about|acap|cap|cid|crid|data|dav|dict|dns|file|ftp|geo|go|gopher|h323|http|https|iax|icap|im|imap|info|ipp|iris|iris.beep|iris.xpc|iris.xpcs|iris.lwz|ldap|mailto|mid|msrp|msrps|mtqp|mupdate|news|nfs|ni|nih|nntp|opaquelocktoken|pop|pres|rtsp|service|session|shttp|sieve|sip|sips|sms|snmp|soap.beep|soap.beeps|tag|tel|telnet|tftp|thismessage|tn3270|tip|tv|urn|vemmi|ws|wss|xcon|xcon-userid|xmlrpc.beep|xmlrpc.beeps|xmpp|z39.50r|z39.50s|adiumxtra|afp|afs|aim|apt|attachment|aw|beshare|bitcoin|bolo|callto|chrome|chrome-extension|com-eventbrite-attendee|content|cvs|dlna-playsingle|dlna-playcontainer|dtn|dvb|ed2k|facetime|feed|finger|fish|gg|git|gizmoproject|gtalk|hcp|icon|ipn|irc|irc6|ircs|itms|jar|jms|keyparc|lastfm|ldaps|magnet|maps|market|message|mms|ms-help|msnim|mumble|mvn|notes|oid|palm|paparazzi|platform|proxy|psyc|query|res|resource|rmi|rsync|rtmp|secondlife|sftp|sgn|skype|smb|soldat|spotify|ssh|steam|svn|teamspeak|things|udp|unreal|ut2004|ventrilo|view-source|webcal|wtai|wyciwyg|xfire|xri|ymsgr):[^<>\x00-\x20]*>", re.IGNORECASE)
        if m:
            # email
            dest = m[1:-1]
            inlines.append(
                Block(t="Link", label=[Block(t="Str", c=dest)], destination="mailto:" + dest))
            return len(m)
        elif m2:
            # link
            dest2 = m2[1:-1]
            inlines.append(
                Block(t="Link", label=[Block(t="Str", c=dest2)], destination=dest2))
            return len(m2)
        else:
            return 0

    def parseHtmlTag(self, inlines):
        """ Attempt to parse a raw HTML tag."""
        m = self.match(reHtmlTag)
        if (m):
            inlines.append(Block(t="Html", c=m))
            return len(m)
        else:
            return 0

    def scanDelims(self, c):
        """ Scan a sequence of characters == c, and return information about
        the number of delimiters and whether they are positioned such that
        they can open and/or close emphasis or strong emphasis.  A utility
        function for strong/emph parsing."""
        numdelims = 0
        first_close_delims = 0
        char_before = char_after = None
        startpos = self.pos

        char_before = '\n' if self.pos == 0 else self.subject[self.pos - 1]

        while (self.peek() == c):
            numdelims += 1
            self.pos += 1

        a = self.peek()
        char_after = a if a else "\\n"

        can_open = (numdelims > 0) and (
            numdelims <= 3) and (not re.match("\s", char_after))
        can_close = (numdelims > 0) and (
            numdelims <= 3) and (not re.match("\s", char_before))

        if (c == "_"):
            can_open = can_open and (
                not re.match("[a-z0-9]", char_before, re.IGNORECASE))
            can_close = can_close and (
                not re.match("[a-z0-9]", char_after, re.IGNORECASE))
        self.pos = startpos
        return {
            "numdelims": numdelims,
            "can_open": can_open,
            "can_close": can_close
        }

    def parseEmphasis(self, inlines):
        """ Attempt to parse emphasis or strong emphasis in an efficient way,
        with no backtracking."""
        startpos = self.pos
        first_close = 0
        nxt = self.peek()
        if ((nxt == "*") or (nxt == "_")):
            c = nxt
        else:
            return 0

        res = self.scanDelims(c)
        numdelims = res["numdelims"]
        self.pos += numdelims
        if startpos > 0:
            inlines.append(
                Block(t="Str", c=self.subject[self.pos - numdelims:numdelims + startpos]))
        else:
            inlines.append(
                Block(t="Str", c=self.subject[self.pos - numdelims:numdelims]))
        delimpos = len(inlines) - 1

        if ((not res["can_open"]) or (numdelims == 0)):
            return 0

        first_close_delims = 0

        if (numdelims == 1):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 1 and res["can_close"]):
                    self.pos += 1
                    inlines[delimpos].t = "Emph"
                    inlines[delimpos].c = inlines[delimpos + 1:]
                    if len(inlines) > 1:
                        for x in range(delimpos + 1, len(inlines)):
                            inlines.pop(len(inlines) - 1)
                    break
                else:
                    if (self.parseInline(inlines) == 0):
                        break
            return (self.pos - startpos)
        elif (numdelims == 2):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 2 and res["can_close"]):
                    self.pos += 2
                    inlines[delimpos].t = "Strong"
                    inlines[delimpos].c = inlines[delimpos + 1:]
                    if len(inlines) > 1:
                        for x in range(delimpos + 1, len(inlines)):
                            inlines.pop(len(inlines) - 1)
                    break
                else:
                    if (self.parseInline(inlines) == 0):
                        break
            return (self.pos - startpos)
        elif (numdelims == 3):
            while (True):
                res = self.scanDelims(c)
                if (res["numdelims"] >= 1 and res["numdelims"] <= 3 and res["can_close"] and not res["numdelims"] == first_close_delims):
                    if first_close_delims == 1 and numdelims > 2:
                        res["numdelims"] = 2
                    elif first_close_delims == 2:
                        res['numdelims'] = 1
                    elif res['numdelims'] == 3:
                        res['numdelims'] = 1
                    self.pos += res['numdelims']

                    if first_close > 0:
                        inlines[
                            delimpos].t = "Strong" if first_close_delims == 1 else "Emph"
                        temp = "Emph" if first_close_delims == 1 else "Strong"
                        inlines[delimpos].c = [Block(t=temp, c=inlines[delimpos + 1:first_close])] + inlines[
                            first_close + 1:]  # error on 362?
                        if len(inlines) > 1:
                            for x in range(delimpos + 1, len(inlines)):
                                inlines.pop(len(inlines) - 1)
                        break
                    else:
                        inlines.append(
                            Block(t="Str", c=self.subject[self.pos - res["numdelims"]:self.pos]))
                        first_close = len(inlines) - 1
                        first_close_delims = res["numdelims"]
                else:
                    if self.parseInline(inlines) == 0:
                        break
            return (self.pos - startpos)
        else:
            return res

        return 0

    def parseLinkTitle(self):
        """ Attempt to parse link title (sans quotes), returning the string
        or null if no match."""
        title = self.match(reLinkTitle)
        if title:
            return unescape(title[1:len(title)-1])
        else:
            return None

    def parseLinkDestination(self):
        """ Attempt to parse link destination, returning the string or
        null if no match."""
        res = self.match(reLinkDestinationBraces)
        if not res is None:
            return unescape(res[1:len(res) - 1])
        else:
            res2 = self.match(reLinkDestination)
            if not res2 is None:
                return unescape(res2)
            else:
                return None

    def parseLinkLabel(self):
        """ Attempt to parse a link label, returning number of characters parsed."""
        if not self.peek() == "[":
            return 0
        startpos = self.pos
        nest_level = 0
        if self.label_nest_level > 0:
            self.label_nest_level -= 1
            return 0
        self.pos += 1
        c = self.peek()
        while ((not c == "]") or (nest_level > 0)) and not c is None:
            if c == "`":
                self.parseBackticks([])
            elif c == "<":
                self.parseAutoLink([]) or self.parseHtmlTag(
                    []) or self.parseString([])
            elif c == "[":
                nest_level += 1
                self.pos += 1
            elif c == "]":
                nest_level -= 1
                self.pos += 1
            elif c == "\\":
                self.parseEscaped([])
            else:
                self.parseString([])
            c = self.peek()
        if c == "]":
            self.label_nest_level = 0
            self.pos += 1
            return self.pos - startpos
        else:
            if c is None:
                self.label_nest_level = nest_level
            self.pos = startpos
            return 0

    def parseRawLabel(self, s):
        """ Parse raw link label, including surrounding [], and return
        inline contents.  (Note:  this is not a method of InlineParser.)"""
        return InlineParser().parse(s[1:-1])

    def parseLink(self, inlines):
        """ Attempt to parse a link.  If successful, add the link to
        inlines."""
        startpos = self.pos
        n = self.parseLinkLabel()

        if n == 0:
            return 0

        afterlabel = self.pos
        rawlabel = self.subject[startpos:n+startpos]

        if self.peek() == "(":
            self.pos += 1
            if self.spnl():
                dest = self.parseLinkDestination()
                if not dest is None and self.spnl():
                    if re.match(r"^\s", self.subject[self.pos - 1]):
                        title = self.parseLinkTitle()
                    else:
                        title = ""
                    if self.spnl() and self.match(r"^\)"):
                        inlines.append(
                            Block(t="Link", destination=dest, title=title, label=self.parseRawLabel(rawlabel)))
                        return self.pos - startpos
                    else:
                        self.pos = startpos
                        return 0
                else:
                    self.pos = startpos
                    return 0
            else:
                self.pos = startpos
                return 0

        savepos = self.pos
        self.spnl()
        beforelabel = self.pos
        n = self.parseLinkLabel()
        if n == 2:
            reflabel = rawlabel
        elif n > 0:
            reflabel = self.subject[beforelabel:beforelabel + n]
        else:
            self.pos = savepos
            reflabel = rawlabel
        if normalizeReference(reflabel) in self.refmap:
            link = self.refmap[normalizeReference(reflabel)]
        else:
            link = None
        if link:
            if link.get("title", None):
                title = link['title']
            else:
                title = ""
            if link.get("destination", None):
                destination = link['destination']
            else:
                destination = ""
            inlines.append(
                Block(t="Link", destination=destination, title=title, label=self.parseRawLabel(rawlabel)))
            return self.pos - startpos
        else:
            self.pos = startpos
            return 0
        self.pos = startpos
        return 0

    def parseEntity(self, inlines):
        """ Attempt to parse an entity, adding to inlines if successful."""
        m = self.match(
            r"^&(?:#x[a-f0-9]{1,8}|#[0-9]{1,8}|[a-z][a-z0-9]{1,31});", re.IGNORECASE)
        if m:
            inlines.append(Block(t="Entity", c=m))
            return len(m)
        else:
            return 0

    def parseString(self, inlines):
        """ Parse a run of ordinary characters, or a single character with
        a special meaning in markdown, as a plain string, adding to inlines."""
        m = self.match(reMain, re.MULTILINE)
        if m:
            inlines.append(Block(t="Str", c=m))
            return len(m)
        else:
            return 0

    def parseNewline(self, inlines):
        """ Parse a newline.  If it was preceded by two spaces, return a hard
        line break; otherwise a soft line break."""
        if (self.peek() == '\n'):
            self.pos += 1
            last = inlines[len(inlines) - 1]
            if last and last.t == "Str" and last.c[-2:] == "  ":
                last.c = re.sub(r' *$', '', last.c)
                inlines.append(Block(t="Hardbreak"))
            else:
                if last and last.t == "Str" and last.c[-1:] == " ":
                    last.c = last.c[0:-1]
                inlines.append(Block(t="Softbreak"))
            return 1
        else:
            return 0

    def parseImage(self, inlines):
        """ Attempt to parse an image.  If the opening '!' is not followed
        by a link, add a literal '!' to inlines."""
        if (self.match("^!")):
            n = self.parseLink(inlines)
            if (n == 0):
                inlines.append(Block(t="Str", c="!"))
                return 1
            elif (inlines[len(inlines) - 1] and
                    (inlines[len(inlines) - 1].t == "Link")):
                inlines[len(inlines) - 1].t = "Image"
                return n + 1
            else:
                raise Exception("Shouldn't happen")
        else:
            return 0

    def parseReference(self, s, refmap):
        """ Attempt to parse a link reference, modifying refmap."""
        self.subject = s
        self.pos = 0
        startpos = self.pos

        matchChars = self.parseLinkLabel()
        if (matchChars == 0):
            return 0
        else:
            rawlabel = self.subject[:matchChars]

        test = self.peek()
        if (test == ":"):
            self.pos += 1
        else:
            self.pos = startpos
            return 0
        self.spnl()

        dest = self.parseLinkDestination()
        if (dest is None or len(dest) == 0):
            self.pos = startpos
            return 0

        beforetitle = self.pos
        self.spnl()
        title = self.parseLinkTitle()
        if (title is None):
            title = ""
            self.pos = beforetitle

        if (self.match(r"^ *(?:\n|$)") is None):
            self.pos = startpos
            return 0

        normlabel = normalizeReference(rawlabel)
        if (not refmap.get(normlabel, None)):
            refmap[normlabel] = {
                "destination": dest,
                "title": title
            }
        return (self.pos - startpos)

    def parseInline(self, inlines):
        """ Parse the next inline element in subject, advancing subject position
        and adding the result to 'inlines'."""
        c = self.peek()
        res = None
        if (c == '\n'):
            res = self.parseNewline(inlines)
        elif (c == "\\"):
            res = self.parseEscaped(inlines)
        elif (c == "`"):
            res = self.parseBackticks(inlines)
        elif ((c == "*") or (c == "_")):
            res = self.parseEmphasis(inlines)
        elif (c == "["):
            res = self.parseLink(inlines)
        elif (c == "!"):
            res = self.parseImage(inlines)
        elif (c == "<"):
            res = self.parseAutoLink(inlines) or self.parseHtmlTag(inlines)
        elif (c == "&"):
            res = self.parseEntity(inlines)
        return res or self.parseString(inlines)

    def parseInlines(self, s, refmap={}):
        """ Parse s as a list of inlines, using refmap to resolve references."""
        self.subject = s
        self.pos = 0
        self.refmap = refmap
        inlines = []
        while (self.parseInline(inlines)):
            pass
        return inlines

    def parse(self, s, refmap={}):
        """ Pass through to parseInlines."""
        return self.parseInlines(s, refmap)


class DocParser:

    def __init__(self, subject=None, pos=0):
        self.doc = Block.makeBlock("Document", 1, 1)
        self.subject = subject
        self.pos = pos
        self.tip = self.doc
        self.refmap = {}
        self.inlineParser = InlineParser()

    def acceptsLines(self, block_type):
        """ Returns true if block type can accept lines of text."""
        return block_type == "Paragraph" or block_type == "IndentedCode" or block_type == "FencedCode"

    def endsWithBlankLine(self, block):
        """ Returns true if block ends with a blank line, descending if needed
        into lists and sublists."""
        if block.last_line_blank:
            return True
        if (block.t == "List" or block.t == "ListItem") and len(block.children) > 0:
            return self.endsWithBlankLine(block.children[len(block.children) - 1])
        else:
            return False

    def breakOutOfLists(self, block, line_number):
        """ Break out of all containing lists, resetting the tip of the
        document to the parent of the highest list, and finalizing
        all the lists.  (This is used to implement the "two blank lines
        break of of all lists" feature.)"""
        b = block
        last_list = None
        while True:
            if (b.t == "List"):
                last_list = b
            b = b.parent
            if not b:
                break

        if (last_list):
            while (not block == last_list):
                self.finalize(block, line_number)
                block = block.parent
            self.finalize(last_list, line_number)
            self.tip = last_list.parent

    def addLine(self, ln, offset):
        """ Add a line to the block at the tip.  We assume the tip
        can accept lines -- that check should be done before calling this."""
        s = ln[offset:]
        if not self.tip.isOpen:
            raise Exception(
                "Attempted to add line (" + ln + ") to closed container.")
        self.tip.strings.append(s)

    def addChild(self, tag, line_number, offset):
        """ Add block of type tag as a child of the tip.  If the tip can't
        accept children, close and finalize it and try its parent,
        and so on til we find a block that can accept children."""
        while not (self.tip.t == "Document" or self.tip.t == "BlockQuote" or self.tip.t == "ListItem" or (self.tip.t == "List" and tag == "ListItem")):
            self.finalize(self.tip, line_number)
        column_number = offset + 1
        newBlock = Block.makeBlock(tag, line_number, column_number)
        self.tip.children.append(newBlock)
        newBlock.parent = self.tip
        self.tip = newBlock
        return newBlock

    def listsMatch(self, list_data, item_data):
        """ Returns true if the two list items are of the same type,
        with the same delimiter and bullet character.  This is used
        in agglomerating list items into lists."""
        return (list_data.get("type", None) == item_data.get("type", None) and
            list_data.get("delimiter", None) == item_data.get("delimiter", None) and
            list_data.get("bullet_char", None) == item_data.get("bullet_char", None))

    def parseListMarker(self, ln, offset):
        """ Parse a list marker and return data on the marker (type,
        start, delimiter, bullet character, padding) or null."""
        rest = ln[offset:]
        data = {}
        blank_item = bool()
        if re.match(reHrule, rest):
            return None
        match = re.search(r'^[*+-]( +|$)', rest)
        match2 = re.search(r'^(\d+)([.)])( +|$)', rest)
        if match:
            spaces_after_marker = len(match.group(1))
            data['type'] = 'Bullet'
            data['bullet_char'] = match.group(0)[0]
            blank_item = match.group(0) == len(rest)
        elif match2:
            spaces_after_marker = len(match2.group(3))
            data['type'] = 'Ordered'
            data['start'] = int(match2.group(1))
            data['delimiter'] = match2.group(2)
            blank_item = match2.group(0) == len(rest)
        else:
            return None
        if spaces_after_marker >= 5 or spaces_after_marker < 1 or blank_item:
            if match:
                data['padding'] = len(match.group(0)) - spaces_after_marker + 1
            elif match2:
                data['padding'] = len(
                    match2.group(0)) - spaces_after_marker + 1
        else:
            if match:
                data['padding'] = len(match.group(0))
            elif match2:
                data['padding'] = len(match2.group(0))
        return data

    def incorporateLine(self, ln, line_number):
        """ Analyze a line of text and update the document appropriately.
        We parse markdown text by calling this on each line of input,
        then finalizing the document."""
        all_matched = True
        offset = 0
        CODE_INDENT = 4
        blank = None
        already_done = False

        container = self.doc
        oldtip = self.tip

        ln = detabLine(ln)

        while len(container.children) > 0:
            last_child = container.children[-1]
            if not last_child.isOpen:
                break
            container = last_child

            match = matchAt(r"[^ ]", ln, offset)
            if match is None:
                first_nonspace = len(ln)
                blank = True
            else:
                first_nonspace = match
                blank = False
            indent = first_nonspace - offset
            if container.t == "BlockQuote":
                matched = bool()
                if len(ln) > first_nonspace and len(ln) > 0:
                    matched = ln[first_nonspace] == ">"
                matched = indent <= 3 and matched
                if matched:
                    offset = first_nonspace + 1
                    try:
                        if ln[offset] == " ":
                            offset += 1
                    except IndexError:
                        pass
                else:
                    all_matched = False
            elif container.t == "ListItem":
                if (indent >= container.list_data['marker_offset'] +
                   container.list_data['padding']):
                    offset += container.list_data[
                        'marker_offset'] + container.list_data['padding']
                elif blank:
                    offset = first_nonspace
                else:
                    all_matched = False
            elif container.t == "IndentedCode":
                if indent >= CODE_INDENT:
                    offset += CODE_INDENT
                elif blank:
                    offset = first_nonspace
                else:
                    all_matched = False
            elif container.t in ["ATXHeader", "SetextHeader", "HorizontalRule"]:
                all_matched = False
            elif container.t == "FencedCode":
                i = container.fence_offset
                while i > 0 and len(ln) > offset and ln[offset] == " ":
                    offset += 1
                    i -= 1
            elif container.t == "HtmlBlock":
                if blank:
                    all_matched = False
            elif container.t == "Paragraph":
                if blank:
                    container.last_line_blank = True
                    all_matched = False
            if not all_matched:
                container = container.parent
                break
        last_matched_container = container

        def closeUnmatchedBlocks(self, already_done, oldtip):
            """ This function is used to finalize and close any unmatched
            blocks.  We aren't ready to do this now, because we might
            have a lazy paragraph continuation, in which case we don't
            want to close unmatched blocks.  So we store this closure for
            use later, when we have more information."""
            while not already_done and not oldtip == last_matched_container:
                self.finalize(oldtip, line_number)
                oldtip = oldtip.parent
            return True, oldtip

        if blank and container.last_line_blank:
            self.breakOutOfLists(container, line_number)
        while not container.t == "FencedCode" and not container.t == "IndentedCode" and not container.t == "HtmlBlock" and not matchAt(r"^[ #`~*+_=<>0-9-]", ln, offset) is None:
            match = matchAt("[^ ]", ln, offset)
            if match is None:
                first_nonspace = len(ln)
                blank = True
            else:
                first_nonspace = match
                blank = False
            ATXmatch = re.search(r"^#{1,6}(?: +|$)", ln[first_nonspace:])
            FENmatch = re.search(
                r"^`{3,}(?!.*`)|^~{3,}(?!.*~)", ln[first_nonspace:])
            PARmatch = re.search(r"^(?:=+|-+) *$", ln[first_nonspace:])
            data = self.parseListMarker(ln, first_nonspace)

            indent = first_nonspace - offset
            if indent >= CODE_INDENT:
                if not self.tip.t == "Paragraph" and not blank:
                    offset += CODE_INDENT
                    already_done, oldtip = closeUnmatchedBlocks(
                        self, already_done, oldtip)
                    container = self.addChild(
                        'IndentedCode', line_number, offset)
                else:
                    break
            elif len(ln) > first_nonspace and ln[first_nonspace] == ">":
                offset = first_nonspace + 1
                try:
                    if ln[offset] == " ":
                        offset += 1
                except IndexError:
                    pass
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild("BlockQuote", line_number, offset)
            elif ATXmatch:
                offset = first_nonspace + len(ATXmatch.group(0))
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "ATXHeader", line_number, first_nonspace)
                container.level = len(ATXmatch.group(0).strip())
                if not re.search(r'\\#', ln[offset:]) is None:
                    container.strings = [
                        re.sub(r'(?:(\\#) *#*| *#+) *$', '\g<1>', ln[offset:])]
                else:
                    container.strings = [
                        re.sub(r'(?:(\\#) *#*| *#+) *$', '', ln[offset:])]
                break
            elif FENmatch:
                fence_length = len(FENmatch.group(0))
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "FencedCode", line_number, first_nonspace)
                container.fence_length = fence_length
                container.fence_char = FENmatch.group(0)[0]
                container.fence_offset = first_nonspace - offset
                offset = first_nonspace + fence_length
                break
            elif not matchAt(reHtmlBlockOpen, ln, first_nonspace) is None:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    'HtmlBlock', line_number, first_nonspace)
                break
            elif container.t == "Paragraph" and len(container.strings) == 1 and PARmatch:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container.t = "SetextHeader"
                container.level = 1 if PARmatch.group(0)[0] == '=' else 2
                offset = len(ln)
            elif not matchAt(reHrule, ln, first_nonspace) is None:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                container = self.addChild(
                    "HorizontalRule", line_number, first_nonspace)
                offset = len(ln) - 1
                break
            elif data:
                already_done, oldtip = closeUnmatchedBlocks(
                    self, already_done, oldtip)
                data['marker_offset'] = indent
                offset = first_nonspace + data['padding']
                if not container.t == "List" or not self.listsMatch(
                   container.list_data, data):
                    container = self.addChild(
                        "List", line_number, first_nonspace)
                    container.list_data = data
                container = self.addChild(
                    "ListItem", line_number, first_nonspace)
                container.list_data = data
            else:
                break
            if self.acceptsLines(container.t):
                break

        match = matchAt(r"[^ ]", ln, offset)
        if match is None:
            first_nonspace = len(ln)
            blank = True
        else:
            first_nonspace = match
            blank = False
        indent = first_nonspace - offset

        if not self.tip == last_matched_container and not blank and self.tip.t == "Paragraph" and len(self.tip.strings) > 0:
            self.last_line_blank = False
            self.addLine(ln, offset)
        else:
            already_done, oldtip = closeUnmatchedBlocks(
                self, already_done, oldtip)
            container.last_line_blank = blank and not (container.t == "BlockQuote" or container.t == "FencedCode" or (
                container.t == "ListItem" and len(container.children) == 0 and container.start_line == line_number))
            cont = container
            while cont.parent:
                cont.parent.last_line_blank = False
                cont = cont.parent
            if container.t == "IndentedCode" or container.t == "HtmlBlock":
                self.addLine(ln, offset)
            elif container.t == "FencedCode":
                match = bool()
                if len(ln) > 0:
                    match = len(ln) > first_nonspace and ln[first_nonspace] == container.fence_char and re.match(
                        r"^(?:`{3,}|~{3,})(?= *$)", ln[first_nonspace:])
                match = indent <= 3 and match
                FENmatch = re.search(
                    r"^(?:`{3,}|~{3,})(?= *$)", ln[first_nonspace:])
                if match and len(FENmatch.group(0)) >= container.fence_length:
                    self.finalize(container, line_number)
                else:
                    self.addLine(ln, offset)
            elif container.t in ["ATXHeader", "SetextHeader", "HtmlBlock"]:
                # nothing to do; we already added the contents.
                pass
            else:
                if self.acceptsLines(container.t):
                    self.addLine(ln, first_nonspace)
                elif blank:
                    pass
                elif not container.t == "HorizontalRule" and not container.t == "SetextHeader":
                    container = self.addChild(
                        "Paragraph", line_number, first_nonspace)
                    self.addLine(ln, first_nonspace)
                else:
                    # print("Line " + str(line_number) +
                    #       " with container type " +
                    #       container.t + " did not match any condition.")
                    pass

    def finalize(self, block, line_number):
        """ Finalize a block.  Close it and do any necessary postprocessing,
        e.g. creating string_content from strings, setting the 'tight'
        or 'loose' status of a list, and parsing the beginnings
        of paragraphs for reference definitions.  Reset the tip to the
        parent of the closed block."""
        if (not block.isOpen):
            return 0

        block.isOpen = False
        if (line_number > block.start_line):
            block.end_line = line_number - 1
        else:
            block.end_line = line_number

        if (block.t == "Paragraph"):
            block.string_content = ""
            for i, line in enumerate(block.strings):
                block.strings[i] = re.sub(r'^  *', '', line, re.MULTILINE)
            block.string_content = '\n'.join(block.strings)

            pos = self.inlineParser.parseReference(
                block.string_content, self.refmap)
            while (block.string_content[0] == "[" and pos):
                block.string_content = block.string_content[pos:]
                if (isBlank(block.string_content)):
                    block.t = "ReferenceDef"
                    break
                pos = self.inlineParser.parseReference(
                    block.string_content, self.refmap)
        elif (block.t in ["ATXHeader", "SetextHeader", "HtmlBlock"]):
            block.string_content = "\n".join(block.strings)
        elif (block.t == "IndentedCode"):
            block.string_content = re.sub(
                r"(\n *)*$", "\n", "\n".join(block.strings))
        elif (block.t == "FencedCode"):
            block.info = unescape(block.strings[0].strip())
            if (len(block.strings) == 1):
                block.string_content = ""
            else:
                block.string_content = "\n".join(block.strings[1:]) + "\n"
        elif (block.t == "List"):
            block.tight = True

            numitems = len(block.children)
            i = 0
            while (i < numitems):
                item = block.children[i]
                last_item = (i == numitems-1)
                if (self.endsWithBlankLine(item) and not last_item):
                    block.tight = False
                    break
                numsubitems = len(item.children)
                j = 0
                while (j < numsubitems):
                    subitem = item.children[j]
                    last_subitem = j == (numsubitems - 1)
                    if (self.endsWithBlankLine(subitem) and
                       not (last_item and last_subitem)):
                        block.tight = False
                        break
                    j += 1
                i += 1
        else:
            pass

        self.tip = block.parent

    def processInlines(self, block):
        """ Walk through a block & children recursively, parsing string content
        into inline content where appropriate."""
        if block.t in ["ATXHeader", "Paragraph", "SetextHeader"]:
            block.inline_content = self.inlineParser.parse(
                block.string_content.strip(), self.refmap)
            block.string_content = ""

        if block.children:
            for i in block.children:
                self.processInlines(i)

    def parse(self, input):
        """ The main parsing function.  Returns a parsed document AST."""
        self.doc = Block.makeBlock("Document", 1, 1)
        self.tip = self.doc
        self.refmap = {}
        lines = re.split(r"\r\n|\n|\r", re.sub(r"\n$", '', input))
        length = len(lines)
        for i in range(length):
            self.incorporateLine(lines[i], i + 1)
        while (self.tip):
            self.finalize(self.tip, length - 1)
        self.processInlines(self.doc)
        return self.doc


class HTMLRenderer(object):
    blocksep = "\n"
    innersep = "\n"
    softbreak = "\n"
    escape_pairs = (("[&]", '&amp;'),
                    ("[<]", '&lt;'),
                    ("[>]", '&gt;'),
                    ('["]', '&quot;'))

    @staticmethod
    def inTags(tag, attribs, contents, selfclosing=None):
        """ Helper function to produce content in a pair of HTML tags."""
        result = "<" + tag
        if (len(attribs) > 0):
            i = 0
            while (len(attribs) > i) and (not attribs[i] is None):
                attrib = attribs[i]
                result += (" " + attrib[0] + '="' + attrib[1] + '"')
                i += 1
        if (len(contents) > 0):
            result += ('>' + contents + '</' + tag + '>')
        elif (selfclosing):
            result += " />"
        else:
            result += ('></' + tag + '>')
        return result

    def __init__(self):
        pass

    def URLescape(self, s):
        """ Escape href URLs."""
        if not re.search("mailto|MAILTO", s):
            if sys.version_info >= (3, 0):
                return re.sub("[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)", "&amp;", HTMLquote(HTMLunescape(s), ":/=*%?&)(#"), re.IGNORECASE)
            else:
                return re.sub("[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)", "&amp;", HTMLquote(HTMLunescape(s).encode("utf-8"), ":/=*%?&)(#"), re.IGNORECASE)
        else:
            return s

    def escape(self, s, preserve_entities=None):
        """ Escape HTML entities."""
        if preserve_entities:
            e = self.escape_pairs[1:]
            s = re.sub(
                "[&](?![#](x[a-f0-9]{1,8}|[0-9]{1,8});|[a-z][a-z0-9]{1,31};)",
                "&amp;", HTMLunescape(s), re.IGNORECASE)
        else:
            e = self.escape_pairs
        for r in e:
            s = re.sub(r[0], r[1], s)
        return s

    def renderInline(self, inline):
        """ Render an inline element as HTML."""
        attrs = None
        if (inline.t == "Str"):
            return self.escape(inline.c)
        elif (inline.t == "Softbreak"):
            return self.softbreak
        elif inline.t == "Hardbreak":
            return self.inTags('br', [], "", True) + "\n"
        elif inline.t == "Emph":
            return self.inTags('em', [], self.renderInlines(inline.c))
        elif inline.t == "Strong":
            return self.inTags("strong", [], self.renderInlines(inline.c))
        elif inline.t == "Html":
            return inline.c
        elif inline.t == "Entity":
            if inline.c == "&nbsp;":
                return " "
            else:
                return self.escape(inline.c, True)
        elif inline.t == "Link":
            attrs = [['href', self.URLescape(inline.destination)]]
            if inline.title:
                attrs.append(['title', self.escape(inline.title, True)])
            return self.inTags('a', attrs, self.renderInlines(inline.label))
        elif inline.t == "Image":
            attrs = [['src', self.escape(inline.destination, True)], [
                     'alt', self.escape(self.renderInlines(inline.label))]]
            if inline.title:
                attrs.append(['title', self.escape(inline.title, True)])
            return self.inTags('img', attrs, "", True)
        elif inline.t == "Code":
            return self.inTags('code', [], self.escape(inline.c))
        else:
            print("Unknown inline type " + inline.t)
            return ""

    def renderInlines(self, inlines):
        """ Render a list of inlines."""
        result = ''
        for i in range(len(inlines)):
            result += self.renderInline(inlines[i])
        return result

    def renderBlock(self,  block, in_tight_list):
        """ Render a single block element."""
        tag = attr = info_words = None
        if (block.t == "Document"):
            whole_doc = self.renderBlocks(block.children)
            if (whole_doc == ""):
                return ""
            else:
                return (whole_doc + "\n")
        elif (block.t == "Paragraph"):
            if (in_tight_list):
                return self.renderInlines(block.inline_content)
            else:
                return self.inTags('p', [],
                                   self.renderInlines(block.inline_content))
        elif (block.t == "BlockQuote"):
            filling = self.renderBlocks(block.children)
            if (filling == ""):
                a = self.innersep
            else:
                a = self.innersep + \
                    self.renderBlocks(block.children) + self.innersep
            return self.inTags('blockquote', [], a)
        elif (block.t == "ListItem"):
            return self.inTags("li", [],
                               self.renderBlocks(block.children,
                                                 in_tight_list).strip())
        elif (block.t == "List"):
            if (block.list_data['type'] == "Bullet"):
                tag = "ul"
            else:
                tag = "ol"
            attr = [] if (not block.list_data.get('start')) or block.list_data[
                'start'] == 1 else [['start', str(block.list_data['start'])]]
            return self.inTags(tag, attr,
                               self.innersep +
                               self.renderBlocks(block.children, block.tight) +
                               self.innersep)
        elif ((block.t == "ATXHeader") or (block.t == "SetextHeader")):
            tag = "h" + str(block.level)
            return self.inTags(tag, [],
                               self.renderInlines(block.inline_content))
        elif (block.t == "IndentedCode"):
            return HTMLRenderer.inTags('pre', [], HTMLRenderer.inTags('code',
                                       [], self.escape(block.string_content)))
        elif (block.t == "FencedCode"):
            info_words = []
            if block.info:
                info_words = re.split(r" +", block.info)
            attr = [] if len(info_words) == 0 else [
                ["class", "language-" + self.escape(info_words[0], True)]]
            return self.inTags('pre', [], self.inTags('code',
                               attr, self.escape(block.string_content)))
        elif (block.t == "HtmlBlock"):
            return block.string_content
        elif (block.t == "ReferenceDef"):
            return ""
        elif (block.t == "HorizontalRule"):
            return self.inTags("hr", [], "", True)
        else:
            print("Unknown block type" + block.t)
            return ""

    def renderBlocks(self, blocks, in_tight_list=None):
        """ Render a list of block elements, separated by this.blocksep."""
        result = []
        for i in range(len(blocks)):
            if not blocks[i].t == "ReferenceDef":
                result.append(self.renderBlock(blocks[i], in_tight_list))
        return self.blocksep.join(result)

    def render(self,  block, in_tight_list=None):
        """ Pass through for renderBlock"""
        return self.renderBlock(block, in_tight_list)