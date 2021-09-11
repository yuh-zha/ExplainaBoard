# Meta-evaluation Dataset for SFRES

## Description
**SFRES** targets utterance generation for spoken
dialogue systems. It contains 581 samples, each sample consists of one
meaning representation, multiple references, and utterances generated by different systems. The human evaluation perspectives are *informativeness*, *naturalness*, *quality*.


## Meta Data
* Github Repo: [jeknov/EMNLP_17_submission](https://github.com/jeknov/EMNLP_17_submission)
* Paper: [Semantically Conditioned LSTM-based Natural Language Generation for Spoken Dialogue Systems](https://aclanthology.org/D15-1199/)
* Aspect: informativeness, naturalness, quality
* Language: English
  
## Data Structure
### Example
We collate the human judgements inside `data.jsonl`. We break down the original dataset by considering each system generation within a new data sample. A data sample is shown in the following json format.


```
{
  "src": "confirm(area=dont_care)",
  "sys_summ": "Do you not to restaurant restaurants that are ?",
  "scores": 
    {
      "informativeness": 1.0, 
      "naturalness": 1.0, 
      "quality": 1.0
    },
 "ref_summs": 
 [
    "This is reference 1.",
    "This is reference 2.",
    ...
  ]
}
```

### Format
Each data sample contains the following fields:
* `src`: Meaning representation.
* `ref_summs`: A list of tokenized, normal-cased reference utterance.
* `sys_summ`: System generated utterance (tokenized, normal-cased).   
* `scores`: For `data.jsonl`, there are only human judgement scores stored as key-value dictionary here. For system output files, the automatic metric scores will also be displayed here (e.g. `{"auto-metric1": 0.2}`). *Since the meaning representations can be the same in different scenarios, we recommend taking the max when aggregating the results based on different reference texts.*


## Reference
```
@inproceedings{wen-etal-2015-semantically,
    title = "Semantically Conditioned {LSTM}-based Natural Language Generation for Spoken Dialogue Systems",
    author = "Wen, Tsung-Hsien  and
      Ga{\v{s}}i{\'c}, Milica  and
      Mrk{\v{s}}i{\'c}, Nikola  and
      Su, Pei-Hao  and
      Vandyke, David  and
      Young, Steve",
    booktitle = "Proceedings of the 2015 Conference on Empirical Methods in Natural Language Processing",
    month = sep,
    year = "2015",
    address = "Lisbon, Portugal",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/D15-1199",
    doi = "10.18653/v1/D15-1199",
    pages = "1711--1721",
}
```