# ExtractBfuStudentsSchedule
Програма на python която извлича програмата за даден курс

## Requirements
- python3
- lxml
- bs4
- requests

## Usage
```python
import extract_bfu_schedule
from extract_bfu_schedule import BfuScheduleExtractor

schedule = BfuScheduleExtractor().extract_schedule(1, 1, 1) #faculty id, form id, level id
#schedule will contain json string representing all lectures for given faculity at level and form
```
