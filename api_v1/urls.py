from django.urls import re_path, include
from . import views


app_name = 'api_v1'

urlpatterns = [
    re_path(r'^$', views.proSearch, name = "proSearch"),
    re_path(r'^pros/$', views.proSearch, name = "proSearch"),
    re_path(r'^pros/(?P<proIds>.+)/$', views.getPROByIDs, name ="getPROByIDs"),
    re_path(r'^proforms/modification/$', views.getAllModifiedForms, name='getAllModifiedForms'),
    re_path(r'^proforms/modification/phosphorylated/$', views.getPhosphorylatedForms, name='getPhosphorylatedFroms'),
    re_path(r'^proforms/modification/methylated/$', views.getMethylatedForms, name='getMethylatedForms'),
    re_path(r'^proforms/modification/acetylated/$', views.getAcetylatedForms, name='getAcetylatedForms'),
    re_path(r'^proforms/modification/ubiquitinated/$', views.getUbiquitinatedForms, name='getUbiquitinatedForms'),
    re_path(r'^proforms/modification/glycosylated/$', views.getGlycosylatedForms, name='getGlycosylatedForms'),
    re_path(r'^proforms/orthoisoform/$', views.getOrthoIsoForms, name='getOrthoIsoForms'),
    re_path(r'^proforms/orthomodform/$', views.getOrthoModForms, name='getOrthoModForms'),
    re_path(r'^proforms/sequence/$', views.getSequenceForms, name='getSequenceForms'),
    re_path(r'^proforms/organism-sequence/$', views.getOrganismSequenceForms, name='getOrganismSequenceForms'),
    re_path(r'^proevos/family/$', views.getFamilyForms, name='getFamilyForms'),
    re_path(r'^proevos/gene/$', views.getGeneForms, name='getGeneForms'),
    re_path(r'^proevos/organism-gene/$', views.getOrganismGeneForms, name='getOrganismGeneForms'),
    re_path(r'^procomps/species-specific/$', views.getSpeciesSpecificComplexForms, name='getSpeciesSpecificComplexForms'),
    re_path(r'^procomps/species-non-specific/$', views.getSpeciesNonSpecificComplexForms, name='getSpeciesNonSpecificComplexForms'),
    re_path(r'^dbxrefs/EcoCyc_ID/$', views.getEcoCycIDs, name= 'getEcoCycIDs'),
    re_path(r'^dbxrefs/HGNC_ID/$', views.getHGNCIDs, name= 'getHGNCIDs'),
    re_path(r'^dbxrefs/MGI_ID/$', views.getMGIIDs, name= 'getMGIIDs'),
    re_path(r'^dbxrefs/Ontology_ID/$', views.getOntologyIDs, name= 'getOntologyIDs'),
    re_path(r'^dbxrefs/PANTHER_ID/$', views.getPANTHERIDs, name= 'getPANTHERIDs'),
    re_path(r'^dbxrefs/PIRSF_ID/$', views.getPIRSFIDs, name= 'getPIRSFIDs'),
    re_path(r'^dbxrefs/PMID/$', views.getPMIDs, name= 'getPMIDs'),
    re_path(r'^dbxrefs/Reactome_ID/$', views.getReactomeIDs, name= 'getReactomeIDs'),
    re_path(r'^dbxrefs/NCBITaxon_ID/$', views.getNCBITaxonIDs, name= 'getNCBITaxonIDs'),
    re_path(r'^dbxrefs/UniProtKB_ID/$', views.getUniProtKBIDs, name= 'getUniProtKBIDs'),
    re_path(r'^paf/(?P<proIds>.+)/$', views.getPAFByIDs, name="getPAFByIDs"),
    re_path(r'^obo/(?P<proIds>.+)/$', views.getOBOByIDs, name="getOBOByIDs"),
    re_path(r'^dag/parent/(?P<proIds>.+)/$', views.getParentByIDs, name="getParentByIDs"),
    re_path(r'^dag/ancestor/(?P<proIds>.+)/$', views.getAncestorByIDs, name="getAncestorByIDs"),
    re_path(r'^dag/children/(?P<proIds>.+)/$', views.getChildrenByIDs, name="getChildrenByIDs"),
    re_path(r'^dag/descendant/(?P<proIds>.+)/$', views.getDescendantByIDs, name="getDescendantByIDs"),
    re_path(r'^dag/hierarchy/(?P<proId>.+)/$', views.getHierarchyByID, name="getHierarchyByID"),
]

