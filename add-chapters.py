#!/usr/bin/env python3
import re
import string
import sys
import yaml
from mutagen import id3
from os import path
from collections import namedtuple

Chapter = namedtuple('Chapter', ['title', 'start', 'end'])

if len(sys.argv) != 2:
  print("Usage: %s path/to.mp3" % sys.argv[0])
  exit(1)

mp3file = sys.argv[1]

def get_episode():
  m = re.match(r"(?:^|.*/)(\d+|\d+.\d).mp3$", mp3file)
  if m is None:
    print("Usage: %s path/to.mp3" % sys.argv[0])
    exit(1)
  n = str(m.group(1))
  for ep in yaml.load_all(open(path.expanduser('episodes.yml'), 'r'), Loader=yaml.FullLoader):
    print(ep)
    if str(ep['episode']) == n:
      return ep

  print("invalid episode number: ", mp3file)
  exit(1)

def parse_time(s):
  m = re.match('(\d+):(\d+):(\d+)', s)
  if m is not None:
    return (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))) * 1000
  m = re.match('(\d+):(\d+)', s)
  if m is not None:
    return (int(m.group(1)) * 60 + int(m.group(2))) * 1000
  print("bad timestamp:", s)
  exit(1)

def get_chapters(ep):
  ret = []
  end = 0xffffffff
  for topic in ep['topics']:
    print(topic)
  for topic in reversed(ep['topics']):
    m = re.match('^([\d:]+)\s(.+)\s*$', topic)
    if m is None:
      continue
    start = parse_time(m.group(1))
    ret.append(Chapter(m.group(2).strip(), start, end))
    end = start
  return list(reversed(ret))

ep = get_episode()

# Add metadata
tag = id3.ID3()
tag.add(id3.TALB(text=[u"あらB.fm"]))
tag.add(id3.TPE1(text=[u"arkbfm"]))
tag.add(id3.TIT2(encoding=id3.Encoding.UTF8, text=['Ep. '+str(ep['episode'])+' '+ep['title']]))

# Add artwork
imagedata = open('cover_art.png', 'rb').read()
tag.add(id3.APIC(3, 'image/png', 3, 'Front cover', imagedata))

# Add chapters
chapters = get_chapters(ep)
if len(chapters) > 0:
  tag.add(id3.CTOC(element_id=u"toc", flags=id3.CTOCFlags.TOP_LEVEL | id3.CTOCFlags.ORDERED,
                   child_element_ids=['chp{:02d}'.format(i) for i in range(len(chapters))],
                   sub_frames=[id3.TIT2(encoding=id3.Encoding.UTF8, text=[u"Table of Contents"])]))

  for i, c in enumerate(chapters):
    tag.add(id3.CHAP(element_id=u'chp{:02d}'.format(i), start_time=c.start, end_time=c.end,
                     sub_frames=[id3.TIT2(encoding=id3.Encoding.UTF8, text=[c.title])]))

tag.save(mp3file)
