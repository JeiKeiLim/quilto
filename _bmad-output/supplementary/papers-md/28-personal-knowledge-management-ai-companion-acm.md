# 28-personal-knowledge-management-ai-companion-acm

**Source:** `28-personal-knowledge-management-ai-companion-acm.pdf`

---

[Latest updates: hps://dl.acm.org/doi/10.1145/3688828.3699647](https://dl.acm.org/doi/10.1145/3688828.3699647)


EXTENDED-ABSTRACT
**From Personal Knowledge Management to the Second Brain to the**
**Personal AI Companian**


**[KONSTANTIN "KOSTA" AAL](https://dl.acm.org/doi/10.1145/contrib-81557694656)** [, University of Siegen, Siegen, Nordrhein-Westfalen, Germany](https://dl.acm.org/doi/10.1145/institution-60024260)


**[SARAH RÜLLER](https://dl.acm.org/doi/10.1145/contrib-99659178936)** [, University of Siegen, Siegen, Nordrhein-Westfalen, Germany](https://dl.acm.org/doi/10.1145/institution-60024260)


**[Open Access Support](https://libraries.acm.org/acmopen)** provided by:


**[University of Siegen](https://dl.acm.org/doi/10.1145/institution-60024260)**



**PDF Download**

**3688828.3699647.pdf**
**01 January 2026**
**Total Citations:** 1

**Total Downloads:** 331


**Published:** 12 January 2025


**[Citation in BibTeX format](https://dl.acm.org/action/exportCiteProcCitation?dois=10.1145%2F3688828.3699647&targetFile=custom-bibtex&format=bibtex)**


[GROUP '25: The 2025 ACM International](https://dl.acm.org/conference/group)

[Conference on Supporting Group Work](https://dl.acm.org/conference/group)
_January 12 - 15, 2025_
_New Jersey, Hilton Head, USA_


**Conference Sponsors:**
[SIGCHI](https://dl.acm.org/sig/sigchi)



GROUP '25: Companion Proceedings of the 2025 ACM International Conference on Supporting Group Work (January 2025)
hps://doi.org/10.1145/3688828.3699647
ISBN: 9798400711879

.


# **From Personal Knowledge Management to the Second Brain to** **the Personal AI Companian**



[Konstantin "Kosta" Aal](https://orcid.org/0000-0001-7693-7340)

Information Systems and New Media
Siegen, NRW, Germany
konstantin.aal@uni-siegen.de


**Abstract**


This extrapolation explores the evolution of Personal Knowledge
Management (PKM) and envisions its future integration with artificial intelligence (AI). As we transition from traditional organizational systems to sophisticated digital ecosystems, the concept of
a ’second brain’ has emerged, exemplified by tools like Evernote
and Notion. However, the integration of AI promises to transform
this concept into an active personal companion. This AI-driven
system would access multiple data streams, creating a rich, interconnected knowledge base that offers personalized insights and
decision support. The paper discusses the potential design of such
an AI companion. Unlike current tools that excel at organizing information, this AI companion would actively engage with data from
various aspects of a user’s life, creating a dynamic, personalized
knowledge overview. While the potential benefits are significant,
the paper also addresses critical considerations, including privacy
concerns, ethical implications, skill requirements for effective use,
and the need to balance human intuition with machine intelligence.
The discussion emphasizes the importance of maintaining user autonomy and critical thinking skills while leveraging AI capabilities.
As we enter "The Intelligence Age," this extrapolation provides a
foundation for further research and discussion on the responsible
development and implementation of AI companions as advanced
cognitive tools, aiming to augment human intelligence rather than
replace it.


**CCS Concepts**


- **Human-centered computing** → _Interaction techniques_ ; **HCI**
**theory, concepts and models** ;


**Keywords**


Personal Knowledge Management, Second Brain, AI, Personal Companion


**ACM Reference Format:**

Konstantin "Kosta" Aal and Sarah Rüller. 2025. From Personal Knowledge
Management to the Second Brain to the Personal AI Companian. In _The 2025_
_ACM International Conference on Supporting Group Work (GROUP Companion_
_’25), January 12–15, 2025, Hilton Head, SC, USA._ ACM, New York, NY, USA,
[4 pages. https://doi.org/10.1145/3688828.3699647](https://doi.org/10.1145/3688828.3699647)


Permission to make digital or hard copies of all or part of this work for personal or
classroom use is granted without fee provided that copies are not made or distributed
for profit or commercial advantage and that copies bear this notice and the full citation
on the first page. Copyrights for third-party components of this work must be honored.
For all other uses, contact the owner/author(s).
_GROUP Companion ’25, January 12–15, 2025, Hilton Head, SC, USA_
© 2025 Copyright held by the owner/author(s).
ACM ISBN 979-8-4007-1187-9/25/01
[https://doi.org/10.1145/3688828.3699647](https://doi.org/10.1145/3688828.3699647)



[Sarah Rüller](https://orcid.org/0000-0003-2541-2776)

Information Systems and New Media
Siegen, Germany
sarah.rueller@uni-siegen.de


**1** **Introduction**


The way we manage knowledge has evolved significantly over the
years, moving from traditional organisational systems to more dynamic, personal methods. Here, human-computer interaction plays
as well an important role, as in every aspect of our life nowadays

[ 1 – 3, 9, 21, 23 – 26 ]. What began as rudimentary personal knowledge
management (PKM) has evolved into sophisticated digital ecosystems to store information. The rise of tools such as Evernote [1],
Notion [2] and others introduced the concept of the ’second brain’

[ 12 ] - a digital extension of our cognitive processes designed to capture and organise our ideas, notes and tasks to alleviate cognitive
overload [17].
This shift towards personal productivity tools aligns with broader
movements such as "quantifying yourself" [ 14, 18 ] where individuals seek to track and optimise various aspects of their lives esp. in
the health sector [ 14 ]. The second brain concept encapsulates this
approach, acting as a comprehensive digital repository of information. It serves not only as a tool for remembering and organising,
but also as a mechanism for connecting different aspects of our
lives, allowing us to make more informed decisions [ 12 ]. However,
this model is set to evolve as artificial intelligence (AI) enters the
picture.
The integration of personalised AI can take this "second brain"
concept to a whole new level, transforming it from a passive information storage system into an active personal companion. Current
tools such as Notion or email clients already help us organise information, but AI promises a more profound interaction with our
knowledge. By accessing multiple data streams - such as emails,
notes, social media activity and even conversations - AI can create a rich, interconnected knowledge base. This enables seamless
access to personalised insights, decisions and ideas based on the
aggregation of an individual’s digital footprint.
In this context, AI transforms from a productivity tool to a cognitive partner. Imagine an AI that doesn’t just store your knowledge,
but dynamically interacts with it, acts as a sparring partner for
your ideas, and critically engages with your thought processes. As
AI becomes more integrated into our daily lives, the second brain
is no longer just a memory aid, but a personal AI companion - a
"friend" that helps with everything from managing daily tasks to
making complex decisions, providing real-time information when
and where it is needed; while there is research around the topic of
the AI companion, the area is underresearched [7, 11, 20].
This publication focuses on current trends in knowledge management and the rise of the machines (also used as a title for the


1 [https://evernote.com](https://evernote.com)
2 [https://www.notion.so/](https://www.notion.so/)



90


GROUP Companion ’25, January 12–15, 2025, Hilton Head, SC, USA Konstantin "Kosta" Aal and Sarah Rüller



Terminator movies [3] ) to extrapolate a possible future. It is therefore not a design fiction, but an extrapolation, trying to provide a
first idea into a direction of research which will be getting more
attention with the current rise of information overload, since we
are entering "The Intelligence Age" [4], stated by Sam Altman.


**2** **State of the Art**


In this section, we briefly review research in the area of PKM and
AI companions. PKM is a critical framework for organising and
harnessing individual knowledge in today’s information-rich world,
and its growing importance is reinforced by the emergence of AI
companions as potential tools for enhancing personal productivity
and creativity.
PKM refers to a systematic process individuals employ to manage and organize their personal knowledge and information effectively. The concept of PKM can be traced back to the work of
Peter Drucker, who first used the terms "knowledge work" and
"knowledge workers" in 1968 [ 8 ]. Drucker’s insights recognised the
growing importance of knowledge as a key resource in modern organisations and the emergence of knowledge workers as a distinct
category of employee. This focus on the significance of individual
knowledge in organisational settings laid the groundwork for the
later development of PKM.
In today’s information-rich environment, PKM is increasingly
essential for coping with the overwhelming volume of data we
encounter daily [ 17 ]. PKM serves as a framework for acquiring,
organizing, and integrating information, transforming it into a
structured personal knowledge base that can be readily accessed
and applied [ 16 ]. By doing so, individuals can categorize, characterize, and define information while understanding the relationships
between various pieces of data. As the sheer volume of information
grows, the ability to retrieve, evaluate, organize, and analyze data
becomes more crucial for personal effectiveness [ 17 ]. PKM helps alleviate the frustration and stress caused by information overload by
making information accessible and usable for decision-making and
problem-solving. For individuals, PKM offers several key benefits,
including increased productivity, improved decision-making, and
enhanced problem-solving abilities [ 13, 16 ]. Effective PKM practices not only streamline personal workflows but also contribute
to the wider organizational knowledge base by fostering better
knowledge sharing, innovation, and overall productivity [ 16, 22 ].
Essential PKM skills include the ability to search and retrieve information, critically assess the credibility and relevance of sources,
organize information efficiently, and analyze it to extract insights.
In addition, collaboration and communication skills are vital for
sharing knowledge and working effectively with others [ 15 ]. While
traditional tools like to-do lists and calendars remain relevant, the
rise of digital tools, such as note-taking apps, web-based platforms,
and semantic search engines, has significantly enhanced PKM capabilities. These tools help individuals efficiently capture, organize,
and retrieve knowledge, making it easier to manage large volumes
of data [15].
However, implementing effective PKM practices can be challenging. A lack of time, awareness, or skills can hinder individuals


3 [https://www.imdb.com/title/tt0181852/](https://www.imdb.com/title/tt0181852/)
4 [https://ia.samaltman.com/](https://ia.samaltman.com/)



from adopting these practices. To overcome these barriers, organizations should promote PKM through training, seminars, and workshops, equipping individuals with the necessary skills to engage
in information management, critical evaluation, and knowledge
synthesis [ 19 ]. Moreover, fostering a supportive environment that
values knowledge management and provides the appropriate infrastructure is crucial for encouraging PKM efforts. The relationship
between PKM and organizational knowledge management is profound [ 15 ]. When individuals are skilled in PKM, they collectively
contribute to a more effective organizational knowledge system,
which in turn enhances innovation, decision-making, and overall
organizational success. Thus, PKM is not just a personal tool for
managing knowledge but a foundational element in creating more
robust, knowledge-driven organizations.
This is followed by the idea of the AI companion, which is an
under-researched area in the field of Human-Computer Interaction
(HCI) and Computer-Supported Cooperative Work (CSCW). While
there are some publications on how AI companions can be used in
different areas such as personal relationships [ 6 ], marketing [ 5 ] and
creative areas such as story writing [ 4 ]. This research shows that AI
is already having a huge impact. The work by De Freitas et al. shows
how AI companions can reduce loneliness by having conversations
through an application on your smartphone and making the person
feel heard. The authors conclude that AI companions can indeed reduce loneliness, suggesting their potential as a scalable solution to
a societal crisis. The research by Biermann et al. provides a diametrically opposed perspective when AI companions were introduced
to the creative process of story writing and had to co-write with
hobbyist and professional writers. The research highlights three
key barriers to the adoption of AI co-writing: writers’ emotional
values (fulfilment, ownership, integrity), perceived competence of
the AI and the writer (mistrust in the AI’s ability to handle complex
writing tasks and confidence in their own abilities), and planning
methods (mismatch between the AI’s control mechanism and the
writer’s preferred planning method). The paper concludes by calling for a nuanced approach to AI companion design that respects
writers’ individual values and writing practices and acknowledges
the need to bridge the gap between AI capabilities and human expectations regarding creative control, trust, and integrity in the
context of collaborative writing [4].
In summary, the integration of PKM and AI companions offers
a compelling opportunity to enhance individual productivity and
creativity in an increasingly complex information landscape. While
PKM equips individuals with essential skills to effectively manage
and synthesise knowledge, AI companions offer innovative support
that can address both emotional needs and creative challenges. The
research highlights the dual potential of AI companions to alleviate
feelings of isolation while transforming collaborative processes in
creative fields. However, successful implementation depends on
understanding and respecting individual values, fostering trust and
bridging the gap between human expectations and AI capabilities.


**3** **Design of the AI Companion**


The next step in the evolution of personal knowledge management
tools is the integration of AI in a deeply networked and proactive
way, moving beyond mere information storage to an intelligent,



91


From Personal Knowledge Management to the Second Brain to the Personal AI Companian GROUP Companion ’25, January 12–15, 2025, Hilton Head, SC, USA


**Figure 2: AI Companion overview**


**4** **Disucssion**



**Figure 1: AI Architecture with the different components and**
**layers**


personal companion. This AI-driven companion will be hosted locally on a server in the user’s home, ensuring privacy and security
through encryption, and accessible through multiple devices, including smartphones, laptops and other digital platforms (see Fig.
1).
Unlike current tools such as Notion [5], Mem.ai [6] and Obsidian [7],
which excel at organising information, this personal companion
will elevate the concept of the "second brain" by functioning as
an AI system that actively engages with and organises data from
every aspect of the user’s life. It will process personal messages
from chat applications, emails, notes, transcripts of conversations,
web articles, YouTube videos, research papers and other forms of
digital content. This AI will create a highly personalised knowledge graph that connects these disparate pieces of information to
provide a more dynamic, insightful perspective on the user’s data.
Over time, this AI companion will not only act as an advanced
second brain, but also evolve into a proactive assistant, offering
contextual suggestions based on calendar events, previous conversations and tasks. For example, it could provide summaries of
previous conversations with friends or colleagues, extract action
points from emails, and help users prepare for upcoming meetings
by highlighting key points from past interactions. The interface,
whether through natural language processing in written or spoken
form, will facilitate seamless interaction, making the AI companion
a sparring partner for brainstorming ideas or revisiting forgotten
knowledge. This level of integration and interactivity is similar to
the vision presented in films such as Her [8], where AI becomes an
integral part of everyday life, providing thoughtful companionship
and support( see Fig. 2).


5 [https://www.notion.so/](https://www.notion.so/)
6 [https://mem.ai/](https://mem.ai/)
7 [https://obsidian.md/](https://obsidian.md/)
8 [https://www.imdb.com/title/tt1798709/](https://www.imdb.com/title/tt1798709/)



The implementation of a personal AI companion as an advanced
’second brain’ raises a number of critical considerations that need
to be addressed to ensure its effective and responsible use.


**4.1** **Privacy concerns**


Privacy is at the forefront of these considerations. The AI companion would have access to a wide range of personal data, including
private messages, emails, notes, transcripts of conversations, browsing history, and more. This level of access raises concerns about
how this data is used, stored and protected. Ensuring that all personal data is processed locally on a home server and encrypted is
essential to prevent unauthorised access and data breaches. Users
need to be confident that their sensitive information will remain
confidential and will not be exposed to external parties or misused
in any way.


**4.2** **Ethical considerations**


Ethical concerns also play an important role in the use of a personal
AI companion. AI’s ability to process and analyse large amounts of
personal data could lead to situations where it ’knows’ more about
the user than the user does. This raises questions about autonomy,
consent and the potential for manipulation, even if unintentional.
There is also the issue of dependency - too much reliance on AI
could impair critical thinking and decision-making skills. Establishing clear ethical guidelines for the operation of AI, including
transparency in how it uses data and makes recommendations, is
crucial to maintaining user trust and ensuring that AI acts in the
user’s best interests.


**4.3** **Skill requirements**

Another challenge is the skill set required to effectively interact
with and benefit from the AI companion. Users may need to develop new skills to work seamlessly with the AI. This includes
understanding how to enter data, interpret the AI’s suggestions
and critically evaluate its conclusions. Because AI can make faster
and more complex connections between ideas than a human can,
users need to be equipped to engage thoughtfully with these insights. User training and support can help bridge this gap, ensuring



92


GROUP Companion ’25, January 12–15, 2025, Hilton Head, SC, USA Konstantin "Kosta" Aal and Sarah Rüller



that AI serves as an empowering tool rather than an overwhelming

presence.


**4.4** **Balancing human and AI interaction**


The advanced capabilities of the AI companion highlight the need
for a balanced relationship between human intuition and machine
intelligence. While AI can significantly improve productivity and
knowledge management by organising data and uncovering relationships, it is essential that users remain actively involved in the
decision-making process. Fostering a collaborative dynamic where
AI assists rather than dictates will help users maintain control over
their personal and professional lives.


**5** **Conclusion**


The evolution of PKM from traditional organisational systems to
sophisticated digital ecosystems marks a significant shift in the
way we deal with information in the modern age. The concept of
a ’second brain’, initially realised through tools such as Evernote
and Notion, has now set the stage for a revolutionary leap forward
with the integration of artificial intelligence.
This extrapolation has explored the potential transformation of
the second brain concept into an AI companion - a cognitive partner
that goes beyond passive information storage to actively engage
with our knowledge base. By harnessing multiple data streams
and creating interconnected knowledge graphs, this AI companion
promises to offer personalised insights, facilitate decision making
and serve as an intellectual sparring partner.
However, implementing such an advanced system is not without
its challenges. Privacy concerns are paramount, requiring robust
security measures such as local processing and encryption. Ethical
considerations around data use, user autonomy and the potential
for over-reliance on AI will need to be carefully addressed. In addition, users will need to develop new skills to effectively interact
with and benefit from these AI companions. This evolution has the
potential to dramatically enhance our cognitive capabilities, but
it also requires us to thoughtfully navigate the ethical and practical implications of integrating AI so deeply into our personal and
professional lives.
As research in this area progresses, it will be crucial to focus on
creating AI companions that augment human intelligence rather
than replace it, and to ensure that these tools empower users to
become more effective thinkers and decision-makers. This extrapolation provides some thoughts for discussion as we enter what
Sam Altman calls "The Intelligence Age". In conclusion, it is essential that researchers actively engage in discussions about how we
will design future AI companions, ensuring that they are just and
inclusive to reflect the pluralistic world we live in [10].


**References**


[1] Konstantin Aal. 2024. _Influence of Social Media in a Changing Landscape of Crisis:_
_Insights into the Digital Dynamics of Conflict and Activism in the Middle Eastern_
_and North African Region_ . Springer Nature.

[2] Tanja Aal, Konstantin Aal, Sonia Perunneparampil, Volker Wulf, and Claudia
Müller. 2023. SpeakOut – A digital platform for orientation and self- help for
personal and social problems of students at university. In _Infrahealth 2023 -_
_Proceedings of the 9th International Conference on Infrastructures in Healthcare_
_2023_ [. European Society for Socially Embedded Technologies (EUSSET). https:](https://doi.org/10.48340/ihc2023_p002)
[//doi.org/10.48340/ihc2023_p002](https://doi.org/10.48340/ihc2023_p002)




[3] Tanja Aal, Laura Scheepmaker, Alicia Julia Wilson Takaoka, Doug Schuler, Alan H.
Borning, Claudia Müller, and Konstantin Aal. 2024. Multispecies Urbanism:
Blueprint on the Methodological Future of Inclusive Smart City Design. In
_Proceedings of 22nd European Conference on Computer-Supported Cooperative_
_Work_ [. European Society for Socially Embedded Technologies (EUSSET). https:](https://doi.org/10.48340/ecscw2024_ws07)
[//doi.org/10.48340/ecscw2024_ws07](https://doi.org/10.48340/ecscw2024_ws07)

[4] Oloff C Biermann, Ning F Ma, and Dongwook Yoon. 2022. From tool to companion: Storywriters want AI writers to respect their personal values and writing
strategies. In _Proceedings of the 2022 ACM Designing Interactive Systems Conference_ .
1209–1227.

[5] Rijul Chaturvedi, Sanjeev Verma, and Vartika Srivastava. 2024. Empowering
AI Companions for Enhanced Relationship Marketing. _California Management_
_Review_ 66, 2 (2024), 65–90.

[6] Julian De Freitas, Ahmet K Uguralp, Zeliha O Uguralp, and Puntoni Stefano. 2024.
AI Companions Reduce Loneliness. _arXiv preprint arXiv:2407.19096_ (2024).

[7] Emmanuel De Salis, Marine Capallera, Quentin Meteier, Leonardo Angelini,
Omar Abou Khaled, Elena Mugellini, Marino Widmer, and Stefano Carrino. 2020.
Designing an AI-companion to support the driver in highly autonomous cars. In
_Human-Computer Interaction. Multimodal and Natural Interaction: Thematic Area,_
_HCI 2020, Held as Part of the 22nd International Conference, HCII 2020, Copenhagen,_
_Denmark, July 19–24, 2020, Proceedings, Part II 22_ . Springer, 335–349.

[8] Peter F Drucker. 1969. The Age of Discontinuity; Guidelines to Our Changing
Society. (1969).

[9] Houda Elmimouni, Yarden Skop, Norah Abokhodair, Sarah Rüller, Konstantin Aal,
Anne Weibert, Adel Al-Dawood, Volker Wulf, and Peter Tolmie. 2024. Shielding
or Silencing?: An Investigation into Content Moderation during the Sheikh Jarrah
Crisis. _Proceedings of the ACM on Human-Computer Interaction_ 8, GROUP (2024),
1–21.

[10] Arturo Escobar. 2018. _Designs for the pluriverse: Radical interdependence, autonomy,_
_and the making of worlds_ . Duke University Press.

[11] Kenneth D Forbus and Thomas R Hinrichs. 2006. Companion cognitive systems:
a step toward Human-Level AI. _AI magazine_ 27, 2 (2006), 83–83.

[12] Tiago Forte. 2022. _Building a second brain: A proven method to organize your_
_digital life and unlock your creative potential_ . Simon and Schuster.

[13] Stuart Garner. 2010. Supporting the personal knowledge management of students
with technology. In _Proceedings of Informing Science & IT Education Conference_
_(InSITE)_ . Citeseer, 237–246.

[14] Henner Gimpel, Marcia Nißen, and Roland Görlitz. 2013. Quantifying the quantified self: A study on the motivations of patients to track their own health.
(2013).

[15] Donald Hislop, Rachelle Bosua, and Remko Helms. 2018. _Knowledge management_
_in organizations: A critical introduction_ . Oxford university press.

[16] Priti Jain. 2011. Personal knowledge management: the foundation of organisational knowledge management. _South African Journal of Libraries and Information_
_Science_ 77, 1 (2011), 1–14.

[17] Theresa L Jefferson. 2006. Taking it personally: personal knowledge management.
_Vine_ 36, 1 (2006), 35–37.

[18] D Lupton. 2016. The quantified self. _Polity_ (2016).

[19] Jerome Martin. 2008. Personal knowledge management: the basis of corporate
and institutional knowledge management.

[20] Kelly Merrill Jr, Jihyun Kim, and Chad Collins. 2022. AI companions for lonely
individuals and the role of social presence. _Communication Research Reports_ 39,
2 (2022), 93–103.

[21] Margarita Osipova, Konstantina Marra, Tanja Aal, Konstantin Aal, Eva Hornecker, and Luke Hespanhol. 2024. The Urban Future is Now: Uniting Powers
for Inclusive and Sustainable Design of Smart Cities. In _Mensch und Computer_
_2024-Workshopband_ . Gesellschaft für Informatik eV, 10–18420.

[22] Liana Razmerita, Kathrin Kirchner, and Frantisek Sudzina. 2009. Personal knowledge management: The role of Web 2.0 tools for managing knowledge at individual and organisational levels. _Online information review_ 33, 6 (2009), 1021–1039.

[23] Sarah Rüller, Konstantin Aal, Norah Abokhodair, Houda Elmimouni, Yarden
Skop, Dave Randall, Nina Boulus-Rodje, Alan Borning, and Volker Wulf. 2024.
Ethnography at the Edge: Exploring Research Dynamics in Crisis and Conflict
Areas. In _Extended Abstracts of the CHI Conference on Human Factors in Computing_
_Systems_ . 1–4.

[24] Sarah Rüller, Konstantin Aal, Peter Tolmie, David Randall, Markus Rohde, and
Volker Wulf. 2023. Rurality and Tourism in Transition: How Digitalization Transforms the Character and Landscape of the Tourist Economy in Rural Morocco.
(2023).

[25] David Unbehaun. 2020. Designing, implementing and evaluating assistive technologies to engage people with dementia and their caregivers. (2020).

[26] David Unbehaun, Aydin Coskun, Jule Jensen, Konstantin Aal, Sarah Rüller, and
Volker Wulf. 2022. Designing Multimodal Augmented- Reality Approaches in
Sports: Collaborative and Competitive Scenarios for Individual and Group-based
Outdoor Interaction. In _Proceedings of 20th European Conference on Computer-_
_Supported Cooperative Work_ . European Society for Socially Embedded Technolo[gies (EUSSET). https://doi.org/10.48340/ecscw2022_p06](https://doi.org/10.48340/ecscw2022_p06)



93


