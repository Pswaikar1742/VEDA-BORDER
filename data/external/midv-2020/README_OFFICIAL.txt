MIDV-2020: A comprehensive benchmark dataset for identity documents analysis

--------------------------------------------------------------------------------

Contents:

1. Abstraсt
2. Structure
3. Contact information
4. Journal reference

--------------------------------------------------------------------------------

1. Abstraсt

Identity documents recognition is an important sub-field of document analysis, 
which deals with tasks of robust document detection, type identification, text 
fields recognition, as well as identity fraud prevention and document 
authenticity validation given photos, scans, or video frames of an identity 
document capture. Significant amount of research has been published on this 
topic in recent years, however a chief difficulty for such research is scarcity 
of datasets, due to the subject matter being protected by security requirements. 

A few datasets of mock identity documents which are available lack diversity of 
document types, capturing conditions, or variability of document field values. 
In addition, the published datasets were typically designed only for a subset of
document recognition problems, not for a complex identity document analysis. 

In this paper, we present a dataset MIDV-2020 which consists of 1000 annotated 
video clips, 1000 scanned images, and 1000 photos of 1000 unique mock identity 
documents, each with unique text field values and unique artificially generated 
faces. For the presented benchmark dataset baselines are provided for such tasks 
as document detection, text fields recognition and end-to-end identity document 
recognition. To date, the proposed dataset is the largest publicly available 
identity documents dataset with variable artificially generated data, and we 
believe that it will prove invaluable for advancement of the field of document 
analysis and recognition.

--------------------------------------------------------------------------------

2. Structure

The set of base document types for MIDV-2020 comprises 10 document types, each 
present in previously published MIDV-500 and MIDV-2019 datasets. The identity 
document types of MIDV-2020 are listed in Table DOCTYPES. 100 sample documents 
were created for each of the 10 document types present in the dataset.

+----+----------------------+-----------------------------+---------------+
| #  | Code                 | Description                 | MIDV-500 code |
+====+======================+=============================+===============+
| 1  | alb_id               | ID Card of Albania          | 01            |
+----+----------------------+-----------------------------+---------------+
| 2  | aze_passport         | Passport of Azerbaijan      | 05            |
+----+----------------------+-----------------------------+---------------+
| 3  | esp_id               | ID Card of Spain            | 21            |
+----+----------------------+-----------------------------+---------------+
| 4  | est_id               | ID Card of Estonia          | 22            |
+----+----------------------+-----------------------------+---------------+
| 5  | fin_id               | ID Card of Finland          | 24            |
+----+----------------------+-----------------------------+---------------+
| 6  | grc_passport         | Passport of Greece          | 25            |
+----+----------------------+-----------------------------+---------------+
| 7  | lva_passport         | Passport of Latvia          | 32            |
+----+----------------------+-----------------------------+---------------+
| 8  | rus_internalpassport | Internal passport of Russia | 39            |
+----+----------------------+-----------------------------+---------------+
| 9  | srb_passport         | Passport of Serbia          | 41            |
+----+----------------------+-----------------------------+---------------+
| 10 | svk_id               | ID Card of Slovakia         | 42            |
+----+----------------------+-----------------------------+---------------+

Original template images are placed in the templates.tar archive:

templates.tar:
  /images/
    /<CODE>/
      00.jpg
      01.jpg
      ...
      99.jpg
    ...
  /annotations/
    <CODE>.json
    ...

Upright scans are placed in the scan_upright.tar archive. The original .tif
scans are placed in the scan_upright_tif.tar:

scan_upright.tar:
  /images/
    /<CODE>/
      00.jpg
      01.jpg
      ...
      99.jpg
    ...
  /annotations/
    <CODE>.json
    ...

scan_upright_tif.tar:
  /images/
    /<CODE>/
      00.tif
      01.tif
      ...
      99.tif

Rotated scans are placed in the same manner in scan_rotated.tar and
scan_rotated_tif.tar:

scan_rotated.tar:
  /images/
    /<CODE>/
      00.jpg
      01.jpg
      ...
      99.jpg
    ...
  /annotations/
    <CODE>.json
    ...

scan_rotated_tif.tar:
  /images/
    /<CODE>/
      00.tif
      01.tif
      ...
      99.tif

Photos are placed in the same manner in photo.tar:

photo.tar:
  /images/
    /<CODE>/
      00.jpg
      01.jpg
      ...
      99.jpg
    ...
  /annotations/
    <CODE>.json
    ...

Photos were captured with different conditions, the condition can be identified
by the photo number:

+--------------------------------------------+-------------+-----------------+
| Capturing conditions and smartphone models | Samsung S10 | Apple iPhone XR |
+============================================+=============+=================+
| Low lighting                               | 80-89       | 70-79           |
+--------------------------------------------+-------------+-----------------+
| Keyboard in the background                 | 35-39       | 30-34           |
+--------------------------------------------+-------------+-----------------+
| Natural lighting, outdoors                 | 45-49       | 40-44           |
+--------------------------------------------+-------------+-----------------+
| Table in the background                    | 55-59       | 50-54           |
+--------------------------------------------+-------------+-----------------+
| Cloth in the background                    | 95-99       | 90-94           |
+--------------------------------------------+-------------+-----------------+
| Text documents in the background           | 25-29       | 20-24           |
+--------------------------------------------+-------------+-----------------+
| Projective distortions                     | 10-19       | 00-09           |
+--------------------------------------------+-------------+-----------------+
| Highlight present                          | 65-69       | 60-64           |
+--------------------------------------------+-------------+-----------------+

Video clips with annotations are placed in clips.tar. The original video clips
are placed in clips_video.tar:

clips.tar:
  /images/
    /<CODE>/
      /00/
        000001.jpg
        000007.jpg
        ...
      /01/
        000001.jpg
        000007.jpg
        ...
      ...
      /99/
        000001.jpg
        000007.jpg
        ...
    ...
  /annotations/
    /<CODE>/
      00.json
      01.json
      ...
      99.json
    ...

clips_video.tar:
  /video/
    /<CODE>/
      00.mp4[MOV]
      01.mp4[MOV]
      ...
      99.mp4[MOV]
    ...

Video clips were captured with different conditions, the condition can be 
identified by the photo number:

+--------------------------------------------+-------------+-----------------+
| Capturing conditions and smartphone models | Samsung S10 | Apple iPhone XR |
+============================================+=============+=================+
| Low lighting                               | 00-09       | 10-19           |
+--------------------------------------------+-------------+-----------------+
| Keyboard in the background                 | 20-24       | 25-29           |
+--------------------------------------------+-------------+-----------------+
| Natural lighting, outdoors                 | 60-64       | 65-69           |
+--------------------------------------------+-------------+-----------------+
| Table in the background                    | 30-34       | 35-39           |
+--------------------------------------------+-------------+-----------------+
| Cloth in the background                    | 40-44       | 45-49           |
+--------------------------------------------+-------------+-----------------+
| Text documents in the background           | 50-54       | 55-59           |
+--------------------------------------------+-------------+-----------------+
| Projective distortions                     | 70-79       | 80-89           |
+--------------------------------------------+-------------+-----------------+
| Highlight present                          | 90-94       | 95-99           |
+--------------------------------------------+-------------+-----------------+

All annotations are made using VGG Image Annotator (VIA) v2.0.11, which can be
obtained via this link: 

https://www.robots.ox.ac.uk/~vgg/software/via/downloads/via-2.0.11.zip

The developer's website: https://www.robots.ox.ac.uk/~vgg/software/via/

--------------------------------------------------------------------------------

7. Contact information

Any questions, complaints, feature requests, etc. can be directed to: 
kbulatov@smartengines.com (Konstantin Bulatov)

--------------------------------------------------------------------------------

4. Journal reference

The article about this dataset is currently under review. When the article is
published, the full reference will be added here.