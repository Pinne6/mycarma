from django.shortcuts import render
import os
import tempfile
import zipfile
from wsgiref.util import FileWrapper
from django.http import HttpResponse, FileResponse
from django.contrib.auth.models import User

# Create your views here.


class FixedFileWrapper(FileWrapper):
    def __iter__(self):
        self.filelike.seek(0)
        return self


def index(request):
    # return render(request, 'carma/../templates/carma/carma.html')
    return render(request, 'carma/../carma/carma.html')


def send_file(request):
    """
    Send a file through Django without loading the whole file into
    memory at once. The FileWrapper will turn the file object into an
    iterator for chunks of 8KB.
    """
    if (request.GET.get('versione') == 'FULL' or request.GET.get('versione') == 'LIGHT') and request.user:
        user_id = User.objects.get(username=request.user.username)
        if user_id.has_perm('simulatore.carma_full') and request.GET.get('versione') == 'FULL':
            filename = "/home/carma/software/" + request.GET.get('file')  # Select your file here.
        elif user_id.has_perm('simulatore.carma_light') and request.GET.get('versione') == 'LIGHT':
            filename = "/home/carma/software/" + request.GET.get('file')  # Select your file here.
        else:
            return
    else:
        return
    wrapper = FileResponse(open(filename, 'rb'))
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=' + request.GET.get('file')
    response['Content-Length'] = os.path.getsize(filename)
    return response


def send_zipfile(request):
    """
    Create a ZIP file on disk and transmit it in chunks of 8KB,
    without loading the whole file into memory. A similar approach can
    be used for large dynamic PDF files.
    """
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for index in range(10):
        filename = __file__  # Select your files here.
        archive.write(filename, 'file%d.txt' % index)
    archive.close()
    wrapper = FileWrapper(file(filename), "rb")
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=test.zip'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response

