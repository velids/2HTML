import os, sys, logging, magic, subprocess, shutil, datetime

reload(sys)
sys.setdefaultencoding('utf8')

UNOCONV = '/usr/bin/unoconv'
PDF2HTMLEX = '/usr/bin/pdf2htmlEX'
UNCOMPRESS = '/usr/bin/7z'

office_types = [
'msword', 				#doc
'vnd.ms-', 				#docm, dotm, xls, xlt, xla, xlam, xlsb, xlsm, xltm, ppam, pptp, potm, ppsm, ppa, pps, pot, ppt
'vnd.oasis.opendocument', 		#odt, odp, ods
'vnd.openxmlformats-officedocument'] 	#docx, dotx, xlsx, xltx, pptx, potx
pdf_types = ['pdf', 'postscript']
compressed_types = ['x-7z', 'x-bzip2', 'x-compress', 'x-gzip', 'x-rar', 'x-tar', 'x-xz',  'zip']

def rng(): #needed, because if tmp is not unique and files are loaded into existing tmp, it will end up "cleaned" afterwards.
	return str(datetime.datetime.now().strftime("%y%m%d_%H%M%S"))

def rm_dir(dir):				                                #removes directory  -V
    if os.path.exists(dir): shutil.rmtree(dir)

def mk_dir(dir):				                                #makes directory  -V
    if not os.path.exists(dir): os.makedirs(dir)
            
def process_pdf(srcfile, dst_dir):		                        #calls pdf2htmlex, passes srcfile, creates output dir if none  -V
    outputfname = os.path.join(dst_dir, str(os.path.basename(srcfile)) + '.html')
    if not os.path.exists(os.path.dirname(outputfname)):
        os.makedirs(os.path.dirname(outputfname))
    try:
        logging.info('PDF2HTMLEX Processing file: ' + str(srcfile))
        subprocess.call([PDF2HTMLEX, '--dest-dir' , '/', srcfile, outputfname], stderr=logging.getLogger().handlers[0].stream )

    except:
        e = sys.exc_info()
        logging.error(str(e))

def process_office (srcfile, dst_dir):
    outputfname = os.path.join(dst_dir, str(os.path.basename(srcfile))+'.pdf')
    try:
	logging.info('UNOCONV Processing file: ' + str(srcfile))
        subprocess.call([UNOCONV, '--format', 'pdf','-eSelectPdfVersion=1','--output', outputfname, srcfile])
    except e: 
	e = sys.exc_info()
	logging.error(str(e))

def process_archive(srcfile, dst_dir, level):		#Is this for compressed files? Use 7z!	 -V
    try:
	logging.info('7z Processing file: ' + str(srcfile))
    	subprocess.call(['7z','x', srcfile,'-o'+dst_dir], stdout=logging.getLogger().handlers[0].stream )
    except e: 
	e = sys.exc_info()
	logging.error(str(e))
#7z x '/home/velid/Desktop/test/Untitled.pdf.zip' -o'/home/velid/Desktop/testresults/' -V


def get_mime_info(filename):
    mime_type = {'main': '', 'sub' : ''}			            #main type / sub type - ex: application/pdf -V
    try:
        mt = magic.from_file(filename, mime=True)		        #gets MimeType of file -V
        if mt and '/' in mt:					
            mime_type['main'], mime_type['sub'] = mt.split('/')	
    except:
        e = sys.exc_info()
        logging.error(str(e))
        
    return mime_type

def get_meta_type(mime_type):					#equivalent of Case1 in my code	-V	
    if mime_type['main'] == 'application':			
        for x in pdf_types:
            if x in mime_type['sub']:
                return 'pdf'
        for x in office_types:
            if x in mime_type['sub']:
                return 'office'
        for x in compressed_types:
            if x in mime_type['sub']:
                return 'archive'
    return 'unknown'        					


def process_dir(src_dir, dst_dir, level):			#changed this part -V, added start_level
    for i in os.listdir(src_dir):
        fname=os.path.join(src_dir, i)
        if not os.path.isdir(fname):				#If not DIR (ergo file) get MimeType/return Subtype -V
            mt = get_mime_info(fname)
            tp = get_meta_type(mt)
            if tp == 'pdf':					#calls PDF2HTMLex -V
                process_pdf(fname, dst_dir)
            if tp == 'office':
		tmp_src_dir = os.path.join(dst_dir, "tmp"+rng())
                process_office(fname, tmp_src_dir)
		process_dir(tmp_src_dir, dst_dir, level)
		rm_dir(tmp_src_dir)
            if tp == 'archive':
                tmp_src_dir = os.path.join(dst_dir, "tmp"+rng()) #Figured I'd just use datetime to cr8 unique temp
                process_archive(fname, tmp_src_dir,level)
                new_dst_dir = os.path.join(dst_dir,i)
                process_dir(tmp_src_dir, new_dst_dir, level)
                rm_dir(tmp_src_dir)
				
        else:							                    #For Nested Files -V
            ndst_dir = fname.replace(src_dir, dst_dir)		
            process_dir(fname, ndst_dir, level)
        
    #return ""

if __name__ == '__main__': #prompts user for input & destination dir
    if len(sys.argv) < 3:
        print "Missing arguments. Use: python " +sys.argv[0] + " --input dir " + " --destination dir"
        exit()
    src_dir = os.path.normpath(sys.argv[1])
    dst_dir = os.path.normpath(sys.argv[2])
    if not os.path.isdir(src_dir) or not os.path.isdir(dst_dir):
        print "First and second argument must be a directory!"
        exit()
	
    mylog = os.path.normpath(dst_dir+"/conversions.log")
    logging.basicConfig(filename=mylog, level=logging.INFO, format= '%(asctime)s - %(message)s')
    logging.info('Started')
    max_depth = 5
    process_dir(src_dir, dst_dir, max_depth)
