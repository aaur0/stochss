try:
  import json
except ImportError:
  from django.utils import simplejson as json

import traceback
from collections import OrderedDict

from stochssapp import *
from stochss.model import *



class SpeciesEditorPage(BaseHandler):

    def get(self):
        all_species = self.get_all_species()

        if all_species is not None:
            self.render_response('modeleditor/specieseditor.html', **all_species)
        else:
            self.render_response('modeleditor/specieseditor.html')


    def post(self):
        # First, check to see if it's an update request and then route it to the appropriate function.
        if self.request.get('update') == "1":
            result = self.update_species()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(result))
            
        elif self.request.get('delete') == "1":
            result = self.delete_species()
            all_species = self.get_all_species()
            if all_species is not None:
                result = dict(result, **all_species)
            self.render_response('modeleditor/specieseditor.html', **result)
                
        else:
            result = self.create_species()
            all_species = self.get_all_species()
            if all_species is not None:
                result = dict(result, **all_species)
            self.render_response('modeleditor/specieseditor.html', **result)

    def create_species(self):
        """
        Create a new species for the current model.
        """
        name = self.request.get('name').strip()
        initial_value = self.request.get('initial_value').strip()

        errors = self.check_input(name, initial_value)
        if errors is not None:
            errors.update({'name': name, 'initial_value': initial_value})
            return errors
        try:
            model = self.get_session_property('model_edited')

            if model is None:
                return {'status': False, 'msg': 'You have not selected any model to edit.'}

            # Check if the species already exists
            if name in model.getAllSpecies():
                return {'status': False, 'msg': 'Species ' + name + ' already exists!', 'name': name, 'initial_value': initial_value}

            species = Species(name, int(initial_value))
            model.addSpecies(species)

            # Update the cache
            self.set_session_property('model_edited', model)
            self.set_session_property('is_model_saved', False)
            return {'status': True, 'msg': 'Species added successfully!'}
        except Exception, e:
            logging.error("species::create_species: Species creation failed with error %s", e)
            traceback.print_exc()
            return {'status': False, 'msg': e}

    def delete_species(self):
        """
        Delete the given species from the current model.
        """
        name = self.request.get('toDelete')        
        try:
            model = self.get_session_property('model_edited')
            model.deleteSpecies(name)

            # Update the cache
            self.set_session_property('model_edited', model)
            self.set_session_property('is_model_saved', False)
            return {'status': True, 'msg': 'Species ' + name + ' deleted successfully!'}
        except Exception, e:
            logging.error("species::delete_species: Species deletion failed with error %s", e)
            traceback.print_exc()
            return {'status': False, 'msg': 'Species deletion failed'}

        
    def check_input(self, name, initial_value):
        """
        Check to see if the input for species creation/updation is valid
        """
        if not name:
            return {'status': False, 'msg': 'Species name is missing!'}

        if not initial_value:
                return {'status': False, 'msg': 'Initial value for species ' + name + ' is missing!'}
        
        # the initial_value must be an integer.        
        try:
            int(initial_value)
        except ValueError:
            return {'status': False, 'msg': 'Initial value for species ' + name + ' is not an integer!'}

        # return None if there are no errors
        return None

    def update_species(self):
        """
        Update the species with new values.
        """
        try:
            model = self.get_session_property('model_edited')
            all_species = model.getAllSpecies()

            # Add the updated values afresh. i.e. The old values are erased.
            new_species_list = []

            index = 1
            for key, value in all_species.items():
                # This param will have the name of the species.
                new_name = self.request.get(str(index) + "-name").strip()
                # The param will have the initial value associated with that key (species name).
                new_initial_value = self.request.get(str(index) + "-initial_value").strip()
                logging.debug('new_name: ' + new_name)
                logging.debug('new_initial_value: ' + new_initial_value)
                # Check to see if there are any error in the input value
                error = self.check_input(new_name, new_initial_value)
                if error is not None:
                    logging.error('error: ' + str(error))
                    return error

                # Add the new entry
                value.name = new_name
                value.initial_value = int(new_initial_value)
                new_species_list.append(value)
                index += 1

            # Delete the old values
            model.deleteAllSpecies()
            # Add the modified species back to the model
            model.addSpecies(new_species_list)
            # Update the cache
            self.set_session_property('model_edited', model)
            self.set_session_property('is_model_saved', False)
            return {'status': True, 'msg': 'Species updated successfully!'}
        except Exception, e:
            logging.error("species::update_species: Updating of Species failed with error %s", e)
            traceback.print_exc()
            return {'status': False, 'msg': e}

    def get_all_species(self):
        """
        Get all the species belonging to the currently edited model.
        This model must be in cache.
        """
        model = self.get_session_property('model_edited')
        if model is None:
            return None
        return {'all_species': model.getAllSpecies()}

