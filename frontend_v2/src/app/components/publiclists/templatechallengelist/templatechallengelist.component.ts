import { Component, HostListener, Inject, OnInit } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { Router, ActivatedRoute } from '@angular/router';
import { DOCUMENT } from '@angular/common';


/**
 * Component Class
 */
@Component({
  selector: 'app-templatechallengelist',
  templateUrl: './templatechallengelist.component.html',
  styleUrls: ['./templatechallengelist.component.scss'],
})
export class TemplatechallengelistComponent implements OnInit {

	 isLoggedIn = false;

   challengeTemplates = [];

   selected_template_id = null;

   templateChallengeCreatePath = '/template-challenge-create';

   templateChallengesFetchPath = 'challenges/get_all_challenge_templates/'


	constructor(
    public authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    @Inject(DOCUMENT) private document,
    private globalService: GlobalService,
    private apiService: ApiService
  ) {}

	ngOnInit() {
		if (this.authService.isLoggedIn()) {
	      this.isLoggedIn = true;
	    }

    this.fetchChallengeTemplates();
	}

  /*
     Template is of form: //(You can use a dummy dict while developing.)
     {
        "title": <title of the challenge template>,
        "image": <preview image of the challenge template>,
        "dataset": <string discribing the dataset>,
        "eval_criteria": <an array or list of strings which are the leaderboard metrics>,
        "phases": <number of challenge phases>,
        "splits": <number of dataset splits>,
        "id": <id_of_challenge_template>
     }
  */
  fetchChallengeTemplates(callback = null) {

    this.apiService.getUrl(this.templateChallengesFetchPath, true, false).subscribe(
      (data) => {
        for(var i = 0; i<data.length; i++){
          this.challengeTemplates.push(data[i]);
        }
      },
      (err)=> {
        this.globalService.showToast('error', 'Sorry, something went wrong when fetching the templates. Please try again later.');
      },
      () => {}
    );
    
    /*
    this.challengeTemplates = [
      {
        'title': 'sample',
        'dataset': 'sample',
        'eval_criteria': ['criterai1'],
        'phases': 2,
        'splits': 2,
        'image': "https://staging-evalai.s3.amazonaws.com/media/logos/fe6779bc-746e-4759-836d-01d25e5cd4f1.jpg",
        'id': 1
      }
    ]
    */
  }
}