from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


def search(request):
    return render(request, 'search.html')


def schema(request):
    return render(request, 'schema.html')


def extraction(request):
    return render(request, 'extraction.html')


def linking(request):
    return render(request, 'linking.html')


def display(request):
    return render(request, 'display.html')


def apis(request):
    return render(request, 'apis.html')


def update(request):
    return render(request, 'update.html')


def contributor(request):
    return render(request, 'contributor.html')


def demos(request):
    return render(request, 'demos.html')


def demo(request, label):
    return render(request, label+'/'+label+'.html')


