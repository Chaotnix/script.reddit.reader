import urllib
import xbmc, xbmcgui
import re, htmlentitydefs
import time
from urllib import urlencode

from default import log, translation, urlMain, itemsPerPage, addonID, subredditsFile

DATEFORMAT = xbmc.getRegion('dateshort')
TIMEFORMAT = xbmc.getRegion('meridiem')


#used to filter out image links if content_type is video (when this addon is called from pictures)
image_exts = ['jpg','png', 'RAW', 'jpeg', 'tiff', 'tga', 'pcx', 'bmp'] #exclude 'gif' as we consider it as gifv


def create_default_subreddits():
    #create a default file and sites
    with open(subredditsFile, 'a') as fh:

        #fh.write('/user/gummywormsyum/m/videoswithsubstance\n')
        fh.write('/user/sallyyy19/m/video[%s]\n' %(translation(32006)))  # user   http://forum.kodi.tv/member.php?action=profile&uid=134499
        fh.write('Documentaries+ArtisanVideos+lectures+LearnUselessTalents\n')
        fh.write('Stop_Motion+FrameByFrame+Brickfilms+Animation\n')
        fh.write('random\n')
        #fh.write('randnsfw\n')
        fh.write('[Frontpage]\n')
        fh.write('popular\n')
        fh.write('gametrailers+tvtrailers+trailers\n')
        fh.write('music+listentothis+musicvideos\n')
        fh.write('site:youtube.com\n')
        fh.write('videos\n')
        #fh.write('videos/new\n')
        fh.write('woahdude+interestingasfuck+shittyrobots\n')


def format_multihub(multihub):
#properly format a multihub string
#make sure input is a valid multihub
    t = multihub
    #t='User/sallyyy19/M/video'
    ls = t.split('/')

    for idx, word in enumerate(ls):
        if word.lower()=='user':ls[idx]='user'
        if word.lower()=='m'   :ls[idx]='m'
    #xbmc.log ("/".join(ls))
    return "/".join(ls)


def this_is_a_multihub(subreddit):
    #subreddits and multihub are stored in the same file
    #i think we can get away with just testing for user/ to determine multihub
    if subreddit.lower().startswith('user/') or subreddit.lower().startswith('/user/'): #user can enter multihub with or without the / in the beginning
        return True
    else:
        return False

def compose_list_item(label,label2,iconImage,property_item_type, onClick_action, infolabels=None  ):
    #build a listitem for use in our custom gui
    #if property_item_type=='script':
    #    property_url is the argument for RunAddon()  and it looks like this:   RunAddon( script.web.viewer, http://m.reddit.com/login )

    liz=xbmcgui.ListItem(label=label,
                         label2=label2,
                         iconImage=iconImage,
                         thumbnailImage=iconImage,
                         path="") #<-- DirectoryItem_url is not used here by the xml gui
    liz.setProperty('item_type', property_item_type)  #item type "script" -> ('RunAddon(%s):' % di_url )


    #liz.setInfo( type='video', infoLabels={"plot": shortcut_description, } )
    liz.setProperty('onClick_action', onClick_action)

    if infolabels==None:
        pass
    else:
        liz.setInfo(type="Video", infoLabels=infolabels)

    return liz


def build_script( mode, url, name="", type="", script_to_call=''):
    #builds the parameter for xbmc.executebuiltin   --> 'RunAddon(script.reddit.reader, ... )'
    if script_to_call: #plugin://plugin.video.reddit_viewer/
        #not used
        #return "plugin://%s/?prl=zaza&%s)" %(script_to_call, "mode="+ mode+"&url="+urllib.quote_plus(url)+"&name="+str(name)+"&type="+str(type) )
        pass
    else:
        #if name.startswith('In style'): log ('    namearg=' + name + ' ' + urllib.quote_plus(name.decode('unicode_escape').encode('ascii','ignore')) )
        #remove unicode characters in name.
        name=name.decode('unicode_escape').encode('ascii','ignore')
        script_to_call=addonID
        return "RunAddon(%s,%s)" %(script_to_call, "mode="+ mode+"&url="+urllib.quote_plus(url)+"&name="+urllib.quote_plus(name)+"&type="+str(type) )

def build_playable_param( mode, url, name="", type="", script_to_call=addonID):
    #builds the  di_url for  pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO); pl.clear();  pl.add(di_url, item) ; xbmc.Player().play(pl, windowed=True)
    return "plugin://" +script_to_call+"mode="+ mode+"&url="+urllib.quote_plus(url)+"&name="+str(name)+"&type="+str(type)

def parse_subreddit_entry(subreddit_entry_from_file):
    #returns subreddit, [alias] and description. also populates WINDOW mailbox for custom view id of subreddit
    #  description= a friendly description of the 'subreddit shortcut' on the first page of addon
    #    used for skins that display them

    subreddit, alias, viewid = subreddit_alias( subreddit_entry_from_file )

    description=subreddit
    #check for domain filter
    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        #log("domain "+ subreddit)
        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        description=translation(32008) % domain            #"Show posts from"

    #describe combined subreddits
    if '+' in subreddit:
        description=subreddit.replace('+','[CR]')

    #describe multireddit or multihub
    if this_is_a_multihub(subreddit):
        description=translation(32007)  #"Custom Multireddit"

    #save that view id in our global mailbox (retrieved by listSubReddit)
    #WINDOW.setProperty('viewid-'+subreddit, viewid)

    return subreddit, alias, description

def subreddit_alias( subreddit_entry_from_file ):
    #users can specify an alias for the subredit and it is stored in the file as a regular string  e.g. diy[do it yourself]
    #this function returns the subreddit without the alias identifier and alias if any or alias=subreddit if none
    ## in addition, users can specify custom viewID for a subreddit by encapsulating the viewid in ()'s

    a=re.compile(r"(\[[^\]]*\])") #this regex only catches the []
    #a=re.compile(r"(\[[^\]]*\])?(\(\d+\))?") #this regex catches the [] and ()'s
    alias=""
    viewid=""
    #return the subreddit without the alias. but (viewid), if present, is still there
    subreddit = a.sub("",subreddit_entry_from_file).strip()
    #log( "  re:" +  subreddit )

    #get the viewID
    try:viewid= subreddit[subreddit.index("(") + 1:subreddit.rindex(")")]
    except:viewid=""
    #log( "viewID=%s for r/%s" %( viewid, subreddit ) )

    if viewid:
        #remove the (viewID) string from subreddit
        subreddit=subreddit.replace( "(%s)"%viewid, "" )

    #get the [alias]
    a= a.findall(subreddit_entry_from_file)
    if a:
        alias=a[0]
        #log( "      alias:" + alias )
    else:
        alias = subreddit

    return subreddit, alias, viewid


def assemble_reddit_filter_string(search_string, subreddit, skip_site_filters="", domain="" ):
    #skip_site_filters -not adding a search query makes your results more like the reddit website
    #search_string will not be used anymore, replaced by domain. leaving it here for now.
    #    using search string to filter by domain returns the same result everyday

    url = urlMain      # global variable urlMain = "http://www.reddit.com"

    if subreddit.startswith('?'):
        #special dev option
        url+='/search.json'+subreddit
        return url

    a=[':','/domain/']
    if any(x in subreddit for x in a):  #search for ':' or '/domain/'
        #log("domain "+ subreddit)
        domain=re.findall(r'(?::|\/domain\/)(.+)',subreddit)[0]
        #log("domain "+ str(domain))

    if domain:
        # put '/?' at the end. looks ugly but works fine.
        #https://www.reddit.com/domain/vimeo.com/?&limit=5
        url+= "/domain/%s/.json?" %(domain)   #/domain doesn't work with /search?q=
    else:
        if this_is_a_multihub(subreddit):
            #e.g: https://www.reddit.com/user/sallyyy19/m/video/search?q=multihub&restrict_sr=on&sort=relevance&t=all
            #https://www.reddit.com/user/sallyyy19/m/video
            #url+='/user/sallyyy19/m/video'
            #format_multihub(subreddit)
            if subreddit.startswith('/'):
                #log("startswith/")
                url+=subreddit  #user can enter multihub with or without the / in the beginning
            else: url+='/'+subreddit
        else:
            if subreddit:
                url+= "/r/"+subreddit
            #else:
                #default to front page instead of r/all
                #url+= "/r/all"
            #   pass

        site_filter=""
        if search_string:
            search_string = urllib.unquote_plus(search_string)
            url+= "/search.json?q=" + urllib.quote_plus(search_string)
        elif skip_site_filters:
            url+= "/.json?"
        else:
            #no more supported_sites filter OR... OR... OR...
            url+= "/.json?"
            pass

    url += "&limit="+str(itemsPerPage)
    #url += "&limit=12"
    #log("assemble_reddit_filter_string="+url)
    return url


def has_multiple_subreddits(content_data_children):
    #check if content['data']['children'] returned by reddit contains a single subreddit or not
    s=""
    #compare the first subreddit with the rest of the list.
    for entry in content_data_children:
        if s:
            if s!=entry['data']['subreddit'].encode('utf-8'):
                #log("  multiple subreddit")
                return True
        else:
            s=entry['data']['subreddit'].encode('utf-8')

    #log("  single subreddit")
    return False

def collect_thumbs( entry ):
    #collect the thumbs from reddit json (not used)
    dictList = []
    keys=['thumb','width','height']
    e=[]

    try:
        e=[ entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
           ,entry['data']['media']['oembed']['thumbnail_width']
           ,entry['data']['media']['oembed']['thumbnail_height']
           ]
        #log('  got 1')
        dictList.append(dict(zip(keys, e)))
    except Exception as e:
        #log( "zz   " + str(e) )
        pass

    try:
        e=[ entry['data']['preview']['images'][0]['source']['url'].encode('utf-8')
           ,entry['data']['preview']['images'][0]['source']['width']
           ,entry['data']['preview']['images'][0]['source']['height']
           ]
        #log('  got 2')
        dictList.append(dict(zip(keys, e)))
    except: pass

    try:
        e=[ entry['data']['thumbnail'].encode('utf-8')        #thumbnail is always in 140px wide (?)
           ,140
           ,0
           ]
        #log('  got 3')
        dictList.append(dict(zip(keys, e)))
    except:
        pass
    #log( json.dumps(dictList, indent=4)  )
    #log( str(dictList)  )
    return

def determine_if_video_media_from_reddit_json( entry ):
    #reads the reddit json and determines if link is a video
    is_a_video=False

    try:
        media_url = entry['data']['media']['oembed']['url']   #+'"'
    except:
        media_url = entry['data']['url']   #+'"'


    # also check  "post_hint" : "rich:video"

    media_url=media_url.split('?')[0] #get rid of the query string
    try:
        zzz = entry['data']['media']['oembed']['type']
        #log("    zzz"+str(idx)+"="+str(zzz))
        if zzz == None:   #usually, entry['data']['media'] is null for not videos but it is also null for gifv especially nsfw
            if ".gifv" in media_url.lower():  #special case for imgur
                is_a_video=True
            else:
                is_a_video=False
        elif zzz == 'video':
            is_a_video=True
        else:
            is_a_video=False
    except:
        is_a_video=False

    return is_a_video

def ret_info_type_icon(info_type, modecommand, domain=''):
    #returns icon for what kind of media the link is.
    #make_addon_url_from() assigns what info_type a url link is.

    #log( "  info_type=%s mode=%s"  %(info_type, modecommand) )

    from domains import sitesBase
    icon="type_unsupp.png"
    if info_type==sitesBase.TYPE_VIDEO:
        icon="type_video.png"
        if modecommand==sitesBase.DI_ACTION_YTDL:
            icon="type_ytdl.png"
        if modecommand==sitesBase.DI_ACTION_URLR:
            icon="type_urlr.png"
        #if 'giphy.com' in domain:
        #    icon="type_giphy.gif"

    elif info_type==sitesBase.TYPE_ALBUM:
        icon="type_album.png"
    elif info_type==sitesBase.TYPE_GIF:
        icon="type_gif.png"
    elif info_type==sitesBase.TYPE_IMAGE:
        icon="type_image.png"
    elif info_type==sitesBase.TYPE_REDDIT:
        icon="alienicon.png"

    return icon

def pretty_datediff(dt1, dt2):
    try:
        diff = dt1 - dt2

        sec_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return 'future'

        if day_diff == 0:
            if sec_diff < 10:
                return translation(32060)     #"just now"
            if sec_diff < 60:
                return str(sec_diff) + translation(32061)      #" secs ago"
            if sec_diff < 120:
                return translation(32062)     #"a min ago"
            if sec_diff < 3600:
                return str(sec_diff / 60) + translation(32063) #" mins ago"
            if sec_diff < 7200:
                return translation(32064)     #"an hour ago"
            if sec_diff < 86400:
                return str(sec_diff / 3600) + translation(32065) #" hrs ago"
        if day_diff == 1:
            return translation(32066)         #"Yesterday"
        if day_diff < 7:
            return str(day_diff) + translation(32067)      #" days ago"
        if day_diff < 31:
            return str(day_diff / 7) + translation(32068)  #" wks ago"
        if day_diff < 365:
            return str(day_diff / 30) + translation(32069) #" months ago"
        return str(day_diff / 365) + translation(32070)    #" years ago"
    except:
        pass


def post_excluded_from( filter, str_to_check):
    #hide posts by domain/subreddit.
    #filter can be subreddit_filter or domain_filter. comma separated string. configured in settings
    #log( '    exclude filter:' +str(filter))
    #log( '    exclude check:' +str_to_check)
    if filter:
        filter_list=filter.split(',')
        filter_list=[x.lower().strip() for x in filter_list]  #  list comprehensions
        #log( '    exclude filter:' +str(filter_list))
        if str_to_check.lower() in filter_list:
            return True
    return False

def add_to_csv_setting(setting_id, string_to_add):
    #adds a string to the end of a setting id in settings.xml
    #this is assuming that it is a comma separated list used in filtering subreddit / domain
    import xbmcaddon
    addon=xbmcaddon.Addon()
    csv_setting=addon.getSetting(setting_id)
    csv_list=csv_setting.split(',')
    csv_list=[x.lower().strip() for x in csv_list]
    csv_list.append(string_to_add)

    csv_list = filter(None, csv_list)                 #removes empty string
    addon.setSetting(setting_id, ",".join(csv_list))

    if setting_id=='domain_filter':
        s=colored_subreddit( string_to_add, 'tan',False )
    elif setting_id=='subreddit_filter':
        s=colored_subreddit( string_to_add )

    xbmc.executebuiltin('XBMC.Notification("%s", "%s" )' %( s, translation(30020)+' '+setting_id.replace('_',' ') ) ) #translation(30020)=Added to

def post_is_filtered_out( entry ):
    from default import hide_nsfw, domain_filter, subreddit_filter

    domain=entry['data']['domain'].encode('utf-8')
    if post_excluded_from( domain_filter, domain ):
        log( '  POST is excluded by domain_filter [%s]' %domain )
        return True

    subreddit=entry['data']['subreddit'].encode('utf-8')
    if post_excluded_from( subreddit_filter, subreddit ):
        log( '  POST is excluded by subreddit_filter [r/%s]' %subreddit )
        return True

    try:    over_18 = entry['data']['over_18']
    except: over_18 = False

    if over_18 and hide_nsfw:
        log( '  POST is excluded by NSFW filter'  )
        return True

    return False

def addtoFilter(to_filter, name, type_of_filter):
    #type_of_filter=domain or subreddit
    from default import domain_filter, subreddit_filter
    if type_of_filter=='domain':
        #log( domain_filter +'+' + to_filter)
        add_to_csv_setting('domain_filter',to_filter)
        pass
    elif type_of_filter=='subreddit':
        #log( subreddit_filter +'+' + to_filter )
        add_to_csv_setting('subreddit_filter',to_filter)
        pass
    else:
        return
    pass

def prettify_reddit_query(subreddit_entry):
    #for search queries; make the reddit query string presentable

    if subreddit_entry.startswith('?'):
        #log('************ prettify_reddit_query='+subreddit_entry)
        tbn=subreddit_entry.split('/')[-1]
        tbn=urllib.unquote_plus(tbn)

        tbn=tbn.replace('?q=','[LIGHT]search:[/LIGHT]' )
        tbn=tbn.replace('site:','' )
        tbn=tbn.replace('&sort=','[LIGHT] sort by:[/LIGHT]' )
        tbn=tbn.replace('&t=','[LIGHT] from:[/LIGHT]' )
        tbn=tbn.replace('subreddit:','r/' )
        tbn=tbn.replace('author:','[LIGHT] by:[/LIGHT]' )
        tbn=tbn.replace('&restrict_sr=on','' )
        tbn=tbn.replace('&restrict_sr=','' )
        tbn=tbn.replace('nsfw:no','' )
        tbn=tbn.replace('nsfw:yes','nsfw' )
        #log('************ prettify_reddit_query='+tbn)
        return tbn
    else:
        return subreddit_entry

def calculate_zoom_slide(img_w, img_h):
    screen_w = 1920
    screen_h = 1080

    startx=0

    #determine how much xbmc would shrink the image to fit screen

    shrink_percent = (float(screen_h) / img_h)
    slide_end = float(img_h-screen_h) * shrink_percent

    log("  shrink_percentage %f " %(shrink_percent) )

    if img_w > screen_w:
        #startx=0

        #*** calc here needs adjustment

        #get the shrunked image width
        s_w=img_w*shrink_percent

        #zoom percent needed to make the shrunked_img_w same as screen_w
        zoom_percent = (float(screen_w) / s_w) - shrink_percent
        log("  percent 2 zoom  %f " %(zoom_percent) )

        #shrunken img height is same as screen_h
        s_h=img_h*shrink_percent  #==screen_h

        #compute not-so-original image height
        nso_h=s_h* zoom_percent
        log("  img h  %f " %(nso_h) )

        slide_end = float(nso_h-screen_h) * 1/zoom_percent   #shrink_percent
    else:
        #startx= (screen_w-img_w) / 2

        #zoom this much to get original size
        zoom_percent = ( float(1) / shrink_percent )

        #zoom_percent = ( float(1.5) / shrink_percent )  #adjust zoom_percent to go from 1:1 to bigger
        #ssp=( float(1.5) / ( float(1) / shrink_percent ) )
        #slide_end = float(img_h-screen_h) * ssp


        log("  percent to zoom  %f " %(zoom_percent) )

    return zoom_percent * 100, slide_end


def parse_filename_and_ext_from_url(url=""):
    filename=""
    ext=""

    from urlparse import urlparse
    path = urlparse(url).path
    #ext = os.path.splitext(path)[1]
    try:
        if '.' in path:
            #log( "        f&e=[%s]" %(url.split('/')[-1]).split('.')[0] )
            #log( "          e=[%s]" %(url.split('/')[-1]).split('.')[-1] )
            filename = path.split('/')[-1].split('.')[0]
            ext      = path.split('/')[-1].split('.')[-1]
            #log( "        ext=[%s]" %ext )
            if not ext=="":

                #ext=ext.split('?')[0]
                ext=re.split("\?|#",ext)[0]

            return filename, ext.lower()
    except:
        pass

    return "", ""

def link_url_is_playable(url):
    ext=ret_url_ext(url)
    if ext in image_exts:
        return 'image'
    if ext in ['mp4','webm','mpg','gifv','gif']:
        return 'video'
            #if ext == 'gif':
            #    return 'gif'
    return False

def ret_url_ext(url):
    if url:
        url=url.split('?')[0]
        #log('        split[0]:' + url)
        if url:
            filename,ext=parse_filename_and_ext_from_url(url)
            #log('        [%s][%s]' %(filename,ext) )
            return ext
    return False

#remove duplicates.  http://stackoverflow.com/questions/7961363/removing-duplicates-in-lists
#The common approach to get a unique collection of items is to use a set.
#  Sets are unordered collections of distinct objects. To create a set from any iterable, you can simply pass it to the built-in set() function.
#  If you later need a real list again, you can similarly pass the set to the list() function.
#entries=list(set(entries))

def remove_duplicates(seq, idfun=None):
    # order preserving https://www.peterbe.com/plog/uniqifiers-benchmark
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def remove_dict_duplicates(list_of_dict, key):

    seen = set()
    return [x for x in list_of_dict if [ x.get(key) not in seen, seen.add(  x.get(key) ) ] [0]]


#http://stackoverflow.com/questions/6330071/safe-casting-in-python
def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default

def cleanTitle(title):
    #replaced by unescape
    title = title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"")
    return title.strip()

def unescape(text):
    ## http://effbot.org/zone/re-sub.htm#unescape-html
    # Removes HTML or XML character references and entities from a text string.
    #
    # @param text The HTML (or XML) source text.
    # @return The plain text, as a Unicode string, if necessary.

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    text=re.sub("&#?\w+;", fixup, text)
    text=text.replace('&nbsp;',' ')
    text=text.replace('\n\n','\n')
    return text

def strip_emoji(text):
    #http://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
    emoji_pattern = re.compile(
        u"(\ud83d[\ude00-\ude4f])|"  # emoticons
        u"(\ud83c[\udf00-\uffff])|"  # symbols & pictographs (1 of 2)
        u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
        u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
        u"(\ud83c[\udde0-\uddff])"  # flags (iOS)
        "+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text) # no emoji

def markdown_to_bbcode(s):
    #https://gist.github.com/sma/1513929
    links = {}
    codes = []
    try:
        #def gather_link(m):
        #    links[m.group(1)]=m.group(2); return ""
        #def replace_link(m):
        #    return "[url=%s]%s[/url]" % (links[m.group(2) or m.group(1)], m.group(1))
        #def gather_code(m):
        #    codes.append(m.group(3)); return "[code=%d]" % len(codes)
        #def replace_code(m):
        #    return "%s" % codes[int(m.group(1)) - 1]

        def translate(p="%s", g=1):
            def inline(m):
                s = m.group(g)
                #s = re.sub(r"(`+)(\s*)(.*?)\2\1", gather_code, s)
                #s = re.sub(r"\[(.*?)\]\[(.*?)\]", replace_link, s)
                #s = re.sub(r"\[(.*?)\]\((.*?)\)", "[url=\\2]\\1[/url]", s)
                #s = re.sub(r"<(https?:\S+)>", "[url=\\1]\\1[/url]", s)
                s = re.sub(r"\B([*_]{2})\b(.+?)\1\B", "[B]\\2[/B]", s)
                s = re.sub(r"\B([*_])\b(.+?)\1\B", "[I]\\2[/I]", s)
                return p % s
            return inline

        #s = re.sub(r"(?m)^\[(.*?)]:\s*(\S+).*$", gather_link, s)
        #s = re.sub(r"(?m)^    (.*)$", "~[code]\\1[/code]", s)
        #s = re.sub(r"(?m)^(\S.*)\n=+\s*$", translate("~[size=200][b]%s[/b][/size]"), s)
        #s = re.sub(r"(?m)^(\S.*)\n-+\s*$", translate("~[size=100][b]%s[/b][/size]"), s)
        s = re.sub(r"(?m)^#{4,6}\s*(.*?)\s*#*$", translate("[LIGHT]%s[/LIGHT]"), s)       #heading4-6 becomed light
        s = re.sub(r"(?m)^#{1,3}\s*(.*?)\s*#*$", translate("[B]%s[/B]"), s)               #heading1-3 becomes bold
        #s = re.sub(r"(?m)^##\s+(.*?)\s*#*$", translate("[B]%s[/B]"), s)
        #s = re.sub(r"(?m)^###\s+(.*?)\s*#*$", translate("[B]%s[/B]"), s)

        s = re.sub(r"(?m)^>\s*(.*)$", translate("|%s"), s)                                #quotes  get pipe character beginning
        #s = re.sub(r"(?m)^[-+*]\s+(.*)$", translate("~[list]\n[*]%s\n[/list]"), s)
        #s = re.sub(r"(?m)^\d+\.\s+(.*)$", translate("~[list=1]\n[*]%s\n[/list]"), s)
        s = re.sub(r"(?m)^((?!~).*)$", translate(), s)
        #s = re.sub(r"(?m)^~\[", "[", s)
        #s = re.sub(r"\[/code]\n\[code(=.*?)?]", "\n", s)
        #s = re.sub(r"\[/quote]\n\[quote]", "\n", s)
        #s = re.sub(r"\[/list]\n\[list(=1)?]\n", "", s)
        #s = re.sub(r"(?m)\[code=(\d+)]", replace_code, s)

        return s
    except:
        return s


def convert_date(stamp):
    #http://forum.kodi.tv/showthread.php?tid=221119
    #used in settings after getting reddit token

    date_time = time.localtime(stamp)
    if DATEFORMAT[1] == 'd':
        localdate = time.strftime('%d-%m-%Y', date_time)
    elif DATEFORMAT[1] == 'm':
        localdate = time.strftime('%m-%d-%Y', date_time)
    else:
        localdate = time.strftime('%Y-%m-%d', date_time)
    if TIMEFORMAT != '/':
        localtime = time.strftime('%I:%M%p', date_time)
    else:
        localtime = time.strftime('%H:%M', date_time)
    return localtime + '  ' + localdate


def xbmcVersion():
    #https://github.com/analogue/mythbox/blob/master/resources/src/mythbox/platform.py
    build = xbmc.getInfoLabel('System.BuildVersion')

    # TODO: regex'ify
    # methods to extract version as number given build string
    methods = [
        lambda b: float(b.split()[0]),               # sample input: 10.1 Git:Unknown
        lambda b: float(b.split()[0].split('-')[1]), # sample input: PRE-11.0 Git:Unknown
        lambda b: float(b.split()[0].split('-')[0]), # sample input: 11.0-BETA1 Git:20111222-22ad8e4
        lambda b: 0.0
    ]

    for m in methods:
        try:
            version = m(build)
            break
        except ValueError:
            # parsing failed, try next method
            pass

    return version


'''
def empty_slideshow_folder():
    for the_file in os.listdir(SlideshowCacheFolder):
        file_path = os.path.join(SlideshowCacheFolder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                #log("deleting:"+file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            log("empty_slideshow_folder error:"+e)
'''

# Recursively follow redirects until there isn't a location header
# Credit to: Zachary Witte @ http://www.zacwitte.com/resolving-http-redirects-in-python
def resolve_http_redirect(url, depth=0):
    if depth > 10:
        raise Exception("Redirected "+depth+" times, giving up.")
    o = urlparse.urlparse(url, allow_fragments=True)
    conn = httplib.HTTPConnection(o.netloc)
    path = o.path
    if o.query:
        path += '?' + o.query
    conn.request("HEAD", path, headers={'User-Agent': YoutubeDLWrapper.std_headers['User-Agent']})
    res = conn.getresponse()
    headers = dict(res.getheaders())
    if 'location' in headers and headers['location'] != url:
        return resolve_http_redirect(headers['location'], depth+1)
    else:
        return url


if __name__ == '__main__':
    pass