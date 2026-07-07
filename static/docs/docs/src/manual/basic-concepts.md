# Basic Concepts

The following are commonly used terms in the PanEval evaluation platform, which help users understand key platform concepts:

## Evaluation Domain

Each model under evaluation typically belongs to a specific domain, meaning that each model is generally designed to perform tasks within a particular field\. The platform currently supports the following domains: NLP \(Natural Language Processing\) and Multimodal\.

## Evaluation Task

A model can perform multiple tasks within a domain\. For example, in the NLP domain, tasks can include English multiple\-choice question answering, Chinese multiple\-choice question answering, English text classification, Chinese text classification, and Chinese open\-domain question answering\.

## Evaluation Object

- **Foundation Model**: A foundation model is pre\-trained on large\-scale unlabeled datasets \(Pre\-Training\) and can be adapted to various downstream tasks after fine\-tuning on a small amount of labeled data\. 

- **Pre\-training Algorithm**: A pre\-training algorithm refers to the technique of training a new model from scratch on large\-scale unlabeled datasets\. Models trained using pre\-training algorithms can capture general patterns and features in the data\. 

- **Fine\-tuning / Compression Algorithms**: Fine\-tuning refers to transfer learning techniques applied to foundation models to adjust model parameters for new tasks\. Compression algorithms aim to reduce model size and improve inference efficiency, including methods such as quantization and pruning\.

## Dataset

A single evaluation task may involve multiple datasets\. For example, in the Chinese text classification task, datasets such as EPRSTMT, TNEWS, OCNLI, and BUSTM are used\. More datasets are continuously being integrated into the platform\. Users can view dataset details by clicking the task name on the homepage\.
