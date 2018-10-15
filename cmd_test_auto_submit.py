#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
<ENTER DESCRIPTION HERE>
"""

from response_auto_handler import handle_survey_response

__author__ = "Jakrin Juangbhanich"
__email__ = "juangbhanich.k@gmail.com"
__version__ = "0.0.0"

if __name__ == "__main__":
    responses = handle_survey_response("SV_5BeysUyOoCyZZSR")
    for r in responses:
        print(r)
