**

## MongoDB - IBM Vision API Lab

This lab is based on the work done by @graboskyc and and adapted to work with the IBM Watson Visual Recognition API.
It shows how to use MongoDB *ChangeStreams* to enrich a MongoDB document by:
  - Subscribing to inserts
  - The image referenced by the "**url**" field of an inserted document is then passed to the [IBM Watson Visual Recognition](https://cloud.ibm.com/docs/services/visual-recognition?topic=visual-recognition-getting-started-tutorial&programming_language=python) Classifier using the [IBM Watson python sdk](https://github.com/watson-developer-cloud/python-sdk)
  - Documents are enriched including labeling and scoring from Watson Visual recognition

In order to be able to succesfully run the python code, make sure the dependencies listed in the requirements.txt are satisfied:

> pip install -r requirements.txt
