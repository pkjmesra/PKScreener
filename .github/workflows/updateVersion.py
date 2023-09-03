"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
import argparse

import mistletoe
from mistletoe.block_token import (BlockCode, BlockToken, CodeFence, Footnote,
                                   Heading, HTMLBlock, List, ListItem,
                                   Paragraph, Quote, SetextHeading, Table,
                                   TableCell, TableRow, ThematicBreak)
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import InlineCode, Link, RawText, SpanToken

argParser = argparse.ArgumentParser()
required = True
argParser.add_argument("-f", "--find", help="Find this item", required=required)
argParser.add_argument(
    "-r", "--replace", help="Replace with this item", required=required
)
argParser.add_argument(
    "-t", "--type", help='Type: One of "link" or "text" type', required=required
)
argParser.add_argument(
    "-p", "--path", help="Relative file path for the file", required=required
)
args = argParser.parse_args()

# args.path='pkscreener/release.md'
# args.find='/0.4/'
# args.replace='/0.41/'
# args.type='link'


def update_text(token: SpanToken):
    """Update the text contents of a span token and its children.
    `InlineCode` tokens are left unchanged."""
    if isinstance(token, RawText) and args.type == "text":
        print(f"Replacing <{args.find}> in <{token.content}> to <{args.replace}>")
        token.content = token.content.replace(args.find, args.replace)
    elif isinstance(token, Link) and args.type == "link":
        print(f"Replacing <{args.find}> in <{token.target}> to <{args.replace}>")
        token.target = token.target.replace(args.find, args.replace)

    if not isinstance(token, InlineCode) and hasattr(token, "children"):
        for child in token.children:
            update_text(child)


def update_block(token: BlockToken):
    """Update the text contents of paragraphs and headings within this block,
    and recursively within its children."""
    if isinstance(
        token,
        (
            Paragraph,
            SetextHeading,
            Heading,
            BlockToken,
            Quote,
            BlockCode,
            CodeFence,
            List,
            ListItem,
            Table,
            TableRow,
            TableCell,
            Footnote,
            ThematicBreak,
            HTMLBlock,
        ),
    ):
        for child in token.children:
            update_text(child)

    for child in token.children:
        if isinstance(
            child,
            (
                Paragraph,
                SetextHeading,
                Heading,
                BlockToken,
                Quote,
                BlockCode,
                CodeFence,
                List,
                ListItem,
                Table,
                TableRow,
                TableCell,
                Footnote,
                ThematicBreak,
                HTMLBlock,
            ),
        ):
            update_block(child)


with open(args.path, "r+") as f:
    with MarkdownRenderer() as renderer:
        document = mistletoe.Document(f)
        update_block(document)
        md = renderer.render(document)
        f.seek(0)
        f.write(md)
        print(md)
        f.truncate()
