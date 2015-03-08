from strip_comments import strip_comments
import re

__all__ = ["split_coq_file_contents", "split_coq_file_contents_with_comments"]

def merge_quotations(statements, sp=' '):
    """If there are an odd number of "s in a statement, assume that we
    broke the middle of a string.  We recombine that string."""

    cur = None
    for i in statements:
        if i.count('"') % 2 != 0:
            if cur is None:
                cur = i
            else:
                yield (cur + sp + i)
                cur = None
        elif cur is None:
            yield i
        else:
            cur += sp + i

BRACES = '{}-*+'

def split_leading_braces(statement):
    while statement.strip() and statement.strip()[0] in BRACES:
        idx = statement.index(statement.strip()[0]) + 1
        first, rest = statement[:idx], statement[idx:]
        yield first
        statement = rest
    if statement:
        yield statement

def split_merge_comments(statements):
    """Find open and close comments."""

    cur = None
    comment_level = 0
    for stmt in statements:
        str_count = 0
        for i in re.split(r'(?<=\*\)) ', stmt.replace('*)', '*) ')):
            if str_count % 2 == 0:
                i2 = re.sub('"[^"]*"|"[^"]*$', '', i)
            else:
                i2 = re.sub('^[^"]*"|"[^"]*"', '', i)
            str_count += i.count('"')
            if '(*' not in i2 and '*)' not in i2:
                if comment_level < 0:
                    if cur is not None:
                        yield cur + i
                        cur = None
                    else:
                        raw_input('UNEXPECTED COMMENT: %s' % i)
                        yield i
                    comment_level = 0
                elif comment_level == 0:
                    if cur is None:
                        for ret in split_leading_braces(i):
                            yield ret
                    else:
                        if ((cur.strip()[:2] == '(*' and cur.strip()[-2:] == '*)') # cur is just a comment
                            or cur.strip()[-1:] in '.}'
                            or cur.strip() in BRACES): # genuine ending
                            yield cur
                            cur = None
                            for ret in split_leading_braces(i):
                                yield ret
                        else:
                            cur += i
                elif cur is None:
                    cur = i
                else:
                    cur += i
            else:
                comment_level += i2.count('(*') - i2.count('*)')
                if cur is None:
                    cur = i
                else:
                    cur += i


def split_coq_file_contents(contents):
    """Splits the contents of a coq file into multiple statements.

    This is done by finding one or three periods followed by
    whitespace.  This is a dumb algorithm, but it seems to be (nearly)
    the one that ProofGeneral and CoqIDE use.

    We additionally merge lines inside of quotations."""
    return list(merge_quotations(re.split('(?<=[^\.]\.\.\.)\s|(?<=[^\.]\.)\s', strip_comments(contents))))

def split_coq_file_contents_with_comments(contents):
    statements = re.split(r'(?<=[^\.]\.\.\.) |(?<=[^\.]\.) ',
                          re.sub(r'((?<=[^\.]\.\.\.)\s|(?<=[^\.]\.)\s)', r' \1', contents))
    return list(split_merge_comments(merge_quotations(statements, sp='')))
