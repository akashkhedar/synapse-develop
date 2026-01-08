"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def organization_people_list(request):
    # Just render the React app - let React handle organization routing
    return render(request, 'home/home.html')


@login_required
def simple_view(request):
    # Just render the React app - let React handle organization routing
    return render(request, 'home/home.html')





