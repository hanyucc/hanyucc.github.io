from enum import Enum
import os
from bs4 import BeautifulSoup

STYLE_ASSETS = [
  'font-awesome/css/font-awesome.css' ,
  'bootstrap.min.css',
  'style.css'
]

class FontAwesomeIcons(str, Enum):
  NONE        = ''
  PDF         = 'fa fa-file-pdf-o'
  ENVELOPE    = 'fa fa-envelope'
  ARCHIVE     = 'fa fa-archive'
  BOOK        = 'fa fa-book'
  GITHUB      = 'fa fa-github'
  ZIP         = 'fa fa-file-archive-o'
  CODE        = 'fa fa-file-code-o'
  COPY        = 'fa fa-clipboard'
  GLOBE       = 'fa fa-globe'
  BACK_ARROW  = 'fa fa-long-arrow-left'
  GRAD_CAP    = 'fa fa-graduation-cap'
  MAP_MARKER  = 'fa fa-map-marker'
  FILE        = 'fa fa-file'
  LINKEDIN    = 'fa fa-linkedin-square'

class Person:
  def __init__(self, name, website = '', me = False):
    self.name = name
    self.website = website
    self.me = me

class Publication:
  def __init__(self,
               image,
               title,
               authors = [],
               joint_authors = {},
               venue = '',
               resources = []):
    self.image = image
    self.title = title
    self.authors = authors
    self.joint_authors = joint_authors
    self.venue = venue
    self.resources = resources

  def get_author_suffix(self, author):
    suffix = ''
    for contribution_suffix, authors in self.joint_authors.items():
      if author in authors:
        suffix = contribution_suffix
    return suffix

  def get_author_names(self):
    names = ''
    for i, author in enumerate(self.authors):
      name = author.name
      name += self.get_author_suffix(author)

      if (author.me):
        names += f'<b>{name}</b>'

      elif (len(author.website) > 0):
        names += f'<a href={author.website}>{name}</a>'

      else:
        names += f'<a href="javascript:void(0)">{name}</a>'

      if i < len(self.authors) - 1:
        names += ', '
      elif i == len(self.authors) - 2:
        names += 'and'

    return names

  def get_resources(self):
    resource_list = ''
    for resource in self.resources:
      resource_list += f'''
        <div class="pr-4">
          <i class="{resource.icon.value}"></i>
          <a href="{resource.path}">
            {resource.name}
          </a>
        </div>
      '''
    return resource_list

class ProjectResources:
  def __init__(self, publication = [], code = []):
    self.publication = publication
    self.code = code

class Resource:
  def __init__(self, icon = FontAwesomeIcons.NONE, path = '', name = ''):
    self.icon = icon
    self.path = path
    self.name = name

class Course:
  def __init__(self, role, name, semesters = []):
    self.role = role
    self.name = name
    self.semesters = semesters

class Video:
  def __init__(self, name, id):
    self.name = name
    self.id = id

class AboutMe:
  def __init__(self, name, name_chinese, image, resources):
    self.name = name
    self.name_chinese = name_chinese
    self.image = image
    self.resources = resources

  def get_html(self):
    links = ''
    for resource in self.resources:
      links += f'''
        <div class="d-block profile-row">
          <i class="{resource.icon.value}"></i> 
          <a
            class="pl-2"
            href="{resource.path}"
          >
            {resource.name}
          </a>
        </div>
      '''
    return f'''
      <div class="d-flex pl-2 pr-2 pt-5 justify-content-start">
        <div>
          <img
            id="profile-pic"
            class="float-left"
            src="{self.image}"
            title=""
            alt="Hanyu"
          />
        </div>
        <div class="col">
          <div class="d-block profile-row">
            <h1 class="name">{self.name}&nbsp;<span style="vertical-align: baseline; font-size: 2.4rem">{self.name_chinese}</span></h1>
          </div>
          {links}
        </div>
      </div>
    '''

class Home:
  def __init__(self, about_me, bio, publications = [], courses = [], music = []):
    self.about_me = about_me
    self.bio = bio
    self.publications = publications
    self.courses = courses
    self.music = music

  def get_music_list_html(self):
    music_list = ''

    for music_link in self.music:
      music_list += f'''
        <iframe src="https://open.spotify.com/embed/track/{music_link}?utm_source=generator&theme=0" width="100%" height="160" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>\n
      '''
    
    music_list =  f'''
      <div class="collapse" id="musicGalleryCollapse">
        <div class="card card-body" style="background-color: #F4F6F5; border-style: none; margin-bottom: 0; text-align: center; padding: 0em; padding-left: 0; padding-right: 0;">
          <div class="music-gallery-grid">
            {music_list}
          </div>
        </div>
      </div>

      <script>
        var musicGalleryCollapse = document.getElementById('musicGalleryCollapse');
        var collapseArrow = document.getElementById('collapseArrow');

        musicGalleryCollapse.addEventListener('show.bs.collapse', function () {{
          collapseArrow.style.transform = 'rotate(90deg)';
        }});
        musicGalleryCollapse.addEventListener('hide.bs.collapse', function () {{
          collapseArrow.style.transform = 'rotate(0deg)';
        }});
      </script>
    '''
    return music_list

  def get_publications_list_html(self):
    pub_list = ''
    for _, pub in self.publications.items():
      # Automatically grab the first resource link (Project or Paper) to act as the main link
      main_link = pub.resources[0].path if len(pub.resources) > 0 else '#'

      pub_list += f'''
        <div>
          <div class="d-flex flex-column flex-md-row pb-4">
            <a href="{main_link}" style="display: block; width: 180px; flex-shrink: 0;">
              <img
                src="{pub.image}"
                class="publication-thumbnail img-responsive img-thumbnail mb-3 mb-md-0"
              />
            </a>
            <div class="d-flex flex-column pl-4">
              <a href="{main_link}" class="text-decoration-none" style="color: inherit;">
                <h5>{pub.title}</h5>
              </a>
              <div>
                {pub.get_author_names()}
              </div>
              <div>
                {pub.venue}
              </div>
              <div class="d-flex flex-row justify-content-start pt-2">
                {pub.get_resources()}
              </div>
            </div>
          </div>
        </div>
      '''
    return pub_list

  def get_teaching_list_html(self):
    teaching_list = ''
    for course in self.courses:
      course_links = ''
      for i in range(len(course.semesters)):
        trailing_mark = '' if i == len(course.semesters) - 1 else ', '
        if len(course.semesters[i].path) > 0:
          course_links += f'''
            <a href="{course.semesters[i].path}">
              {course.semesters[i].name + trailing_mark}
            </a>
          '''
        else:
          course_links += f'''
            {course.semesters[i].name + trailing_mark}
          '''
      teaching_list += f'''
          <div class="d-flex flex-row pb-3">
            <div class="d-flex flex-column pl-3">
              <div>
                {course.name}
              </div>
              <div>
                {course.role}, {course_links}
              </div>
            </div>
          </div>
      '''


    return teaching_list

  def generate(self, path):
    soup = BeautifulSoup('<!DOCTYPE html> <html></html>', 'html.parser')

    # add styling
    head = soup.new_tag('head')
    soup.html.append(head)
    links = [
      soup.new_tag('link', rel='stylesheet', type='text/css',
                   href=os.path.join('assets', style_asset))
      for style_asset in STYLE_ASSETS
    ]
    [head.append(link) for link in links]

    head.append(BeautifulSoup(f'<title>{self.about_me.name}</title>', 'html.parser'))

    # construct page
    body = soup.new_tag('body')
    soup.html.append(body)
    about_me_section = self.about_me.get_html()
    publications_list = self.get_publications_list_html()
    teaching_list = self.get_teaching_list_html()
    music_list = self.get_music_list_html()

    body.append(BeautifulSoup('''
      <!-- Google tag (gtag.js) -->
      <script async src="https://www.googletagmanager.com/gtag/js?id=G-THS1KHKPTC"></script>
      <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'G-THS1KHKPTC');
      </script>
    ''', 'html.parser'))

    body.append(BeautifulSoup(f'''
      <div class="container">
        {about_me_section}
      </div>
      <div class="container">
        <div class="d-flex flex-column pl-2 pr-2 pt-3">
          <div>
            <p>{self.bio} <span style="margin: 0 5px; color: #8A9A92;">—</span> <a class="text-decoration-none" data-bs-toggle="collapse" href="#musicGalleryCollapse" role="button" aria-expanded="false" aria-controls="musicGalleryCollapse" style="color: #8A9A92;"> some music that i like <span id="collapseArrow" style="color: #8A9A92; display:inline-block; transition: transform 0.3s; transform-origin: 60% 60%;">&raquo;</span></a></p>
          </div>
          {music_list}
          <div class="pt-2">
            <h3>Publications</h3>
            <hr/>
            <div id="publications-list" class="pt-1">
              {publications_list}
            </div>
          </div>
          <div>
            <h3>Teaching</h3>
            <hr/>
            {teaching_list}
          </div>
        </div>

        <div class="faux-footer"></div>
        <div class="bottom-centered">
          Design and source code based on <br><a href="https://www.bailey-miller.com/">Bailey Miller's website</a>.
        </div>

        <script src="assets/bootstrap.bundle.min.js"></script>
      </div>
    ''', 'html.parser'))
    with open(os.path.join(path, 'index.html'), 'w', encoding='utf-8') as file:
      file.write(str(soup))

PEOPLE = {
  'hanyu-chen': Person(
    name = 'Hanyu Chen',
    website = 'https://hanyuc.com',
    me = True
  ),
  'ioannis-gkioulekas': Person(
    name = 'Ioannis Gkioulekas',
    website = 'https://www.cs.cmu.edu/~igkioule/'
  ),
  'bailey-miller': Person(
    name = 'Bailey Miller',
    website = 'https://www.bailey-miller.com/'
  ),
  'alice-lai': Person(
    name = 'Alice Lai',
    website = 'https://www.linkedin.com/in/alicelai5/'
  ),
  'amber-xiangli': Person(
    name = 'Yuanbo Xiangli',
    website = 'https://kam1107.github.io/'
  ),
  'ruojin-cai': Person(
    name = 'Ruojin Cai',
    website = 'https://www.cs.cornell.edu/~ruojin/'
  ),
  'jeffrey-byrne': Person(
    name = 'Jeffrey Byrne',
    website = 'https://www.jeffreybyrne.com/'
  ),
  'noah-snavely': Person(
    name = 'Noah Snavely',
    website = 'https://www.cs.cornell.edu/~snavely/'
  ),
  'jingsen-zhu': Person(
    name = 'Jingsen Zhu',
    website = 'https://jingsenzhu.github.io/'
  ),
  'joy-zhang': Person(
    name = 'Joy Xiaoji Zhang',
    website = 'https://www.cs.cornell.edu/~joyxiaojizhang/'
  ),
  'steve-marschner': Person(
    name = 'Steve Marschner',
    website = 'https://www.cs.cornell.edu/~srm/'
  ),
  'xueqing-tsang': Person(
    name = 'Xueqing Tsang'
  )
}

ABOUT_ME = AboutMe(
  name = 'Hanyu Chen',
  name_chinese = '陈涵宇',
  image = 'data/images/profile.jpg',
  resources=[
    # Resource(
    #   icon=FontAwesomeIcons.MAP_MARKER,
    #   name='Carnegie-Mellon University',
    #   path='https://www.cs.cmu.edu'
    # ),
    Resource(
      icon=FontAwesomeIcons.ENVELOPE,
      name='Email',
      path='mailto:hanyuc@cs.cornell.edu'
    ),
    Resource(
      icon=FontAwesomeIcons.GITHUB,
      name='Github',
      path='https://github.com/hanyucc'
    ),
    Resource(
      icon=FontAwesomeIcons.GRAD_CAP,
      name='Google Scholar',
      path='https://scholar.google.com/citations?user=pyISEOcAAAAJ&hl=en'
    ),
    Resource(
      icon=FontAwesomeIcons.LINKEDIN,
      name='LinkedIn',
      path='https://www.linkedin.com/in/hanyu-chen-9ba563179/'
    ),
    Resource(
      icon=FontAwesomeIcons.FILE,
      name='CV',
      path='data/documents/cv.pdf'
    )
  ]
)

BIO = '''
I am a second-year Ph.D. student in Computer Science at <a href="https://www.cornell.edu/">Cornell University</a>, advised by Professor <a href="https://www.cs.cornell.edu/~snavely/">Noah Snavely</a>.
Before starting my Ph.D., I received my M.S. and B.S. in Computer Science from <a href="https://www.cmu.edu/">Carnegie Mellon University</a>, where I was advised by Professor <a href="https://www.cs.cmu.edu/~igkioule/">Ioannis Gkioulekas</a>.
My research interest lies in differentiable and neural rendering for 3D reconstruction, and more broadly at the intersection of graphics and 3D vision.
'''

PUBLICATIONS = {
  'pub6': Publication(
    image =  'data/images/thumbnails/metricscenes.png',
    title =  'Honey, I Shrunk the Arc de Triomphe!',
    authors =  [
      PEOPLE['amber-xiangli'],
      PEOPLE['hanyu-chen'],
      PEOPLE['xueqing-tsang'],
      PEOPLE['noah-snavely']
    ],
    venue = 'European Conference on Computer Vision (ECCV), 2026',
    resources = [
      Resource(
        icon = FontAwesomeIcons.GLOBE,
        name = 'project',
        path = 'https://metricscenes.github.io/'
      ),
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/metricscenes.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2606.02379'
      )
    ]
  ),
  'pub5': Publication(
    image =  'data/images/thumbnails/archsym.png',
    title =  'ArchSym: Detecting 3D-Grounded Architectural Symmetries in the Wild',
    authors =  [
      PEOPLE['hanyu-chen'],
      PEOPLE['ruojin-cai'],
      PEOPLE['steve-marschner'],
      PEOPLE['noah-snavely']
    ],
    venue = 'IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2026',
    resources = [
      Resource(
        icon = FontAwesomeIcons.GLOBE,
        name = 'project',
        path = 'https://hanyuc.com/archsym/'
      ),
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/archsym.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2604.22202'
      )
    ]
  ),
  'pub4': Publication(
    image =  'data/images/thumbnails/hairformer.png',
    title =  'HairFormer: Transformer-Based Dynamic Neural Hair Simulation',
    authors =  [
      PEOPLE['joy-zhang'],
      PEOPLE['jingsen-zhu'],
      PEOPLE['hanyu-chen'],
      PEOPLE['steve-marschner']
    ],
    venue = 'arXiv preprint, 2025',
    resources = [
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/hairformer.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2507.12600'
      )
    ]
  ),
  'pub3': Publication(
    image =  'data/images/thumbnails/dopp++.png',
    title =  'Doppelgangers++: Improved Visual Disambiguation with Geometric 3D Features',
    authors =  [
      PEOPLE['amber-xiangli'],
      PEOPLE['ruojin-cai'],
      PEOPLE['hanyu-chen'],
      PEOPLE['jeffrey-byrne'],
      PEOPLE['noah-snavely']
    ],
    venue = 'IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2025 <br><span class="award-highlight">(highlight)</span>',
    resources = [
      Resource(
        icon = FontAwesomeIcons.GLOBE,
        name = 'project',
        path = 'https://doppelgangers25.github.io/doppelgangers_plusplus/'
      ),
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/doppelgangers_plusplus.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2412.05826'
      )
    ]
  ),
  'pub2': Publication(
    image =  'data/images/thumbnails/fast_dipole_sums.png',
    title =  '3D Reconstruction with Fast Dipole Sums',
    authors =  [
      PEOPLE['hanyu-chen'],
      PEOPLE['bailey-miller'],
      PEOPLE['ioannis-gkioulekas']
    ],
    venue = 'ACM Transactions on Graphics (SIGGRAPH Asia), 2024',
    resources = [
      Resource(
        icon = FontAwesomeIcons.GLOBE,
        name = 'project',
        path = 'https://imaging.cs.cmu.edu/fast_dipole_sums'
      ),
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/fast_dipole_sums.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2405.16788'
      )
    ]
  ),
  'pub1': Publication(
    image =  'data/images/thumbnails/volumetric_opaque_solids.png',
    title =  'Objects as Volumes: A Stochastic Geometry View of Opaque Solids',
    authors =  [
      PEOPLE['bailey-miller'],
      PEOPLE['hanyu-chen'],
      PEOPLE['alice-lai'],
      PEOPLE['ioannis-gkioulekas']
    ],
    venue = 'IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), 2024 <br><span class="award-highlight">(best student paper honorable mention)</span>',
    resources = [
      Resource(
        icon = FontAwesomeIcons.GLOBE,
        name = 'project',
        path = 'https://imaging.cs.cmu.edu/volumetric_opaque_solids'
      ),
      Resource(
        icon = FontAwesomeIcons.PDF,
        name = 'paper',
        path = 'data/papers/volumetric_opaque_solids.pdf'
      ),
      Resource(
        icon = FontAwesomeIcons.BOOK,
        name = 'arXiv',
        path = 'https://arxiv.org/abs/2312.15406'
      )
    ]
  )
}

COURSES = [
  Course(
    role = 'Teaching Assistant',
    name = 'Data Structures and Functional Programming (Cornell CS 3110)',
    semesters = [
      Resource(
        name='Spring 2025',
        path='https://www.cs.cornell.edu/courses/cs3110/2025sp/'
      )
    ]
  ),
  Course(
    role = 'Teaching Assistant',
    name = 'Computer Graphics Practicum (Cornell CS 4621)',
    semesters = [
      Resource(
        name='Fall 2024',
        path='https://classes.cornell.edu/browse/roster/FA24/class/CS/4621'
      )
    ]
  ),
  Course(
    role = 'Teaching Assistant',
    name = 'Physics-based Rendering (CMU 15-468/668/868)',
    semesters = [
      Resource(
        name='Spring 2023',
        path='http://graphics.cs.cmu.edu/courses/15-468/2023_spring/'
      )
    ]
  ),
  Course(
    role = 'Grader',
    name = 'Algebraic Structures (CMU 21-373)',
    semesters = [
      Resource(
        name='Fall 2022',
        path='http://coursecatalog.web.cmu.edu/schools-colleges/melloncollegeofscience/departmentofmathematicalsciences/courses/#:~:text=21%2D373%20Algebraic%20Structures')
    ]
  )
]

MUSIC = ['4SrRrB27n7fiRkQcPoKfpk', '1bAZV1EBTRi9t1cVg75i8t', '2nZ33CKRbgpJQJJQKHuGXb', '6tVahG14lCjexVQnYWKgwF', '7CqleiaEqHVazV19P532X9', '7Jh1bpe76CNTCgdgAdBw4Z']

if __name__ == '__main__':
  directory = 'hanyuc.com/'
  if not os.path.exists(directory):
    os.makedirs(directory)

  home = Home(about_me=ABOUT_ME,
              bio=BIO,
              publications=PUBLICATIONS,
              courses=COURSES,
              music=MUSIC)
  home.generate(directory)
