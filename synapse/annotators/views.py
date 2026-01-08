from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def annotator_test_page(request):
    """
    Test page for annotators to complete their qualification test.
    This is a React-based page that will use the test APIs.
    """
    # Check if user is an annotator
    if not request.user.is_annotator:
        from django.shortcuts import redirect

        return redirect("projects:project-index")

    # Render the public template which will load the React app
    return render(request, "home/home_public.html")





