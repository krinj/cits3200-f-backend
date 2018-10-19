#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
<ENTER DESCRIPTION HERE>
"""

from response import get_survey_responses

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"
__version__ = "0.0.0"

if __name__ == "__main__":
    mode = "ALL_RESPONSES"
    responses = get_survey_responses(
        mode,
        "SV_5BeysUyOoCyZZSR",
        "c4JmqD2ohMRIbRNXTqd6YQmHlvxIBiVvV2eekgqo",
        "ca1")

    for r in responses:
        print(r)
