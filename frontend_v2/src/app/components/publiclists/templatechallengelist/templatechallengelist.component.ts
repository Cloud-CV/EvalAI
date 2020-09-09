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
export class TemplateChallengeListComponent implements OnInit {

  /**
   * Is the user logged in?
   */
  isLoggedIn = false;

  /**
   * All the challenge templates are stored here
   */
  challengeTemplates = [];

  /**
   * Path to create a template based challenge
   */
  templateChallengeCreatePath = '/template-challenge-create';

  /**
   * Path to fetch all challenge templates
   */
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
     Template is of form:
     {
        "title": <title of the challenge template>,
        "image": <preview image of the challenge template>,
        "dataset": <string discribing the dataset>,
        "eval_metrics": <an array or list of strings which are the leaderboard metrics>,
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
  }
}
