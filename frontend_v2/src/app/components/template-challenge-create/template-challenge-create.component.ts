import { Component, OnInit, ViewChildren, QueryList, Inject } from '@angular/core';

import { AuthService } from '../../services/auth.service';
import { ApiService } from '../../services/api.service';
import { GlobalService } from '../../services/global.service';
import { ChallengeService } from '../../services/challenge.service';
import { Router, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-template-challenge-create',
  templateUrl: './template-challenge-create.component.html',
  styleUrls: ['./template-challenge-create.component.scss'],
})
export class TemplateChallengeCreateComponent implements OnInit {

	 isLoggedIn = false;

	 hostTeam = 2; // Initialize this using the 

	 id = null;
	 phases = null;

	 challengeData = {
	 	'title': null,
	 	'start_date': null,
	 	'end_date': null,
	 	'description': null,
	 	'evaluation_script': null,
	 	'challenge_phases': []
	 }

	 challengePhaseData = {
	 	'name': null,
	 	'start_date': null,
	 	'end_date': null
	 }

	 hostedChallengesRoute = '/challenges/me';


	constructor(
    public authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private challengeService: ChallengeService,
    @Inject(DOCUMENT) private document,
    private globalService: GlobalService,
    private apiService: ApiService
  ) {}

	ngOnInit() {
		if (this.authService.isLoggedIn()) {
	      this.isLoggedIn = true;
	    }

	    this.route.params.subscribe((params) => {
	      if (params['id']) {
	        this.id = params['id'];
	      }

	      if (params['phases']){
	      	this.phases = params['phases'];
	      }

	      if (params['hostTeam']){
	      	this.hostTeam = params['hostTeam'];
	      }

	    });

	    for(var i = 0; i<this.phases; i++){
	    	this.challengePhaseData['id'] = i+1;
	    	this.challengeData['challenge_phases'].push(Object.assign({}, this.challengePhaseData));
	    };
	}

	

	createTemplateChallenge(){
		if (this.challengeData != null) {
			const FORM_DATA: FormData = new FormData();
			this.challengeData['is_template_challenge'] = true;
			this.challengeData['template_id'] = this.id
			FORM_DATA.append('data', JSON.stringify(this.challengeData));
			this.globalService.startLoader('Creating Challenge');
			this.challengeService.challengeCreate(this.hostTeam, FORM_DATA).subscribe(
		        (data) => {
		          this.globalService.stopLoader();
		          this.globalService.showToast('success', 'Challenge created and successfuly sent to EvalAI admin for approval.');
		          this.router.navigate([this.hostedChallengesRoute]);
		        },
		        (err) => {
		          this.globalService.stopLoader();
		          this.globalService.showToast('error', "Sorry, something went wrong when creating the challenge. Please try again later.");
		        },
		        () => {}
		      );
		}
		else {
			this.globalService.showToast('error', 'Please fill all the given challenge details');
		}
	}
}