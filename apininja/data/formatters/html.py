from apininja.data.formatters import Formatter
from apininja.data import *
from apininja.helpers import *
import urllib

def get_user_attributes(item):
    attrs = get_user_attributes_orig(item)
    return list(sorted(attrs,key=lambda a:a.ui.display_order))
    
default_template_path = 'apininja/data/formatters/template.html'
    
# class HtmlFormatter(Formatter):
    # mime_types=['text/html']
    # format='html'
    # template_path = ''

    # def decode(self,data,**kwargs):
        # raw= urllib.parse.parse_qs(data)
        # for prop,val in raw.items():
            # if isinstance(val,list) and len(val) ==1:
                # raw[prop]=val[0]
        # return raw
    
    # def encode(self,data):
        # if isinstance(data,Exception):
            # return self.encode_error(data,user)
        # elif isinstance(data,DataObject):
            # # if '$action' in kwargs:
                # # action = kwargs['$action']
                # # if action == '$create':
                    # # return self.create_form(data,user,**kwargs)
                # # elif action == '$edit':
                    # # return self.edit_form(data,user,**kwargs)
                # # elif action == '$delete':
                    # # return self.delete_form(data,user,**kwargs)
                # # else:
                    # # raise ValueError('Unknown action type %s'%action)
            # # elif isinstance(data,DataContainer):
                # # return self.encode_table(data,user,**kwargs)
            # # else:
            # return self.encode_view(data,user)
        # else:
            # values = {
            # 'content':str(data),
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':''
            # }
            # output= self.template % values
            # return output

    # def encode_error(self,data,user,**kwargs):
        # title = 'Error';
        # if 'status' in kwargs:
            # title = str(kwargs['status']) +' '+title
        # values = {
        # 'content':str(data),
        # 'app_name':config['DEFAULT']['application_name'],
        # 'description':config['DEFAULT']['description'],
        # 'url':config['HTTP']['host_name'],
        # 'title':title
        # }
        # output= self.template % values
        # return output

    # def get_attributes(self,data,user):
        # vals = []
        # if isinstance(data,DataObject):
            # for attr in data.attributes:
                # if attr.user_can_read(user) and attr.name[0]!='_':
                    # vals.append(attr.name)
        # elif isinstance(data,dict):
            # for x in data.keys():
                # if x[0]!='_':
                    # vals.append(x)
        # else:
            # for x in dir(data):
                # if x[0]!='_':
                    # vals.append(x)
        # return vals

    # def encode_table(self,data,user,**kwargs):    
        # frags = []
        # items = list(data)
        # title = data.web_path
        # frags.append(table_for(data))
        # if len(data) == 0:
            # frags.append('<h2>No data here</h2><strong>I\'m lonely</strong>')
        
        # frags.append(div(create_for(data)))      
        
        # values = {
            # 'content':'\n'.join(frags),
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':title
            # }
        # output= self.template % values
        # return output

    # def encode_view(self,data):
        # title = 'View %s' % data.web_path
        
        # data_type = type(data)
        
        # properties = get_user_attributes(data)
        # frags = [ view_for(data,**kwargs)]
        # frags.append('<div>')
        # frags.append(edit_for(data))
        # frags.append(delete_for(data))
        # frags.append('</div>')
        
        # values = {
            # 'content':'\n'.join(frags),
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':title
            # }
        # output= self.template % values
        # return output

    # def delete_form(self,data,user,**kwargs):
        # p = data.web_path
        # title = 'edit %s'%p
        # properties = get_user_attributes(data)
        # frags = []
        # frags.append('<form method="POST">')
        # frags.append(self.render_view(properties,data,user,**kwargs))
        
        # frags.append('<input type="hidden" id="_id" name="_id" value="%s" />'%data.id)
        # frags.append(a('Cancel',data.parent.path,**{'class':'btn'}))
        # frags.append(input('submit','submit','Delete',**{'class':'btn btn-danger'}))
        # frags.append('</form>')
        
        # values = {
            # 'content':'\n'.join(frags),
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':title
            # }
        # output= self.template % values
        # return output

    # def create_form(self,data,user,**kwargs):
        # t = data.item_data_type
        # title = 'new '+t.name
        # item = data.create_item({})
        # properties = get_user_attributes(item)
        # content = self.render_form(properties,item,user,**kwargs)        
        
        # values = {
            # 'content':content,
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':title
            # }
        # output= self.template % values
        # return output

    # def edit_form(self,data,user,**kwargs):
        # p = data.web_path
        # title = p
        # properties = get_user_attributes(data)
        # content = self.render_form(properties,data,user,**kwargs)        
        
        # values = {
            # 'content':content,
            # 'app_name':config['DEFAULT']['application_name'],
            # 'description':config['DEFAULT']['description'],
            # 'url':config['HTTP']['host_name'],
            # 'title':title
            # }
        # output= self.template % values
        # return output

    # def render_form(self,properties,data,user,**kwargs):
        # frags = []
        # frags.append('<form method="POST">')
        # id = data.id if data and data.id else ''
        # frags.append('<input class="span2" type="hidden" id="_id" name="_id" value="%s" />' % id)
        # for prop in properties:
            # if prop.name[0] == '_': continue
            # elif prop.readonly: continue
            # val = ''
            # if data is None:
                # val = prop.default
            # else:
                # val = getattr(data,prop.name,'')
            # if val is None:
                # val=''
            
            # if not prop.data_type or issimple(prop.data_type):
                # ctrl = control_for(prop,val,**{'class':'span3'})
            # elif data:
                # ctrl = link_for(data,prop)
            
            # frags.append(div(
                # label_for(prop,**{'class':'span2'}),
                # ctrl,
                # **{'class':'row'})
                # )
        # frags.append('<div class="offset3"><a href="/%s" class="btn">Cancel</a><input type="submit" class="btn btn-success" value="Save"/></div>'%data.parent.web_path)
        # frags.append('</form>')
        # return '\n'.join(frags)
    
    
    # def render_view(self,properties,data,user,**kwargs):
        # frags = []
        # frags.append('<div>')
        # for prop in properties:
            # val = ''
            # if data is None:
                # val = prop.default
            # else:
                # val = getattr(data,prop.name,'')
            # if val is None:
                # val=''
            # frags.append('<div>')
            # frags.append('<p><strong>%s</strong></p>'%prop.name)
            # if issimple(prop.data_type):
                # frags.append('<p>%s</p>'%val)
            # else:
                # frags.append(link_for(data,prop))
                
            # frags.append('</div>')
        # frags.append('</div>')
        # return '\n'.join(frags)
