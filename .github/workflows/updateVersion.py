import argparse
import mistletoe
from mistletoe.block_token import BlockToken, Heading, Paragraph, SetextHeading
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import InlineCode, RawText, SpanToken, Link
argParser = argparse.ArgumentParser()
args = argParser.parse_args()

argParser.add_argument('-f', '--find', help='Find this item', required=False)
argParser.add_argument('-r', '--replace', help='Replace with this item', required=False)
argParser.add_argument('-t', '--type', help='Type: One of "link" or "text" type', required=False)
argParser.add_argument('-f', '--filepath', help='Relative file path for the file', required=False)

def update_text(token: SpanToken):
    """Update the text contents of a span token and its children.
    `InlineCode` tokens are left unchanged."""
    if isinstance(token, RawText):
        token.content = token.content.replace(args.find, args.replace)

    if not isinstance(token, InlineCode) and hasattr(token, "children"):
        for child in token.children:
            update_text(child)

def update_link(token: SpanToken):
    """Update the text contents of a span token and its children.
    `InlineCode` tokens are left unchanged."""
    if isinstance(token, Link):
        token.target = token.target.replace(args.find, args.replace)

    if not isinstance(token, InlineCode) and hasattr(token, "children"):
        for child in token.children:
            update_link(child)

def update_block(token: BlockToken):
    """Update the text contents of paragraphs and headings within this block,
    and recursively within its children."""
    if isinstance(token, (Paragraph, SetextHeading, Heading)):
        for child in token.children:
            if args.type == 'text':
                update_text(child)
            if args.type == 'link':
                update_link(child)

    for child in token.children:
        if isinstance(child, BlockToken):
            update_block(child)

with open(args.filepath, "r") as fin:
    with MarkdownRenderer() as renderer:
        document = mistletoe.Document(fin)
        update_block(document)
        md = renderer.render(document)
        print(md)