import { Component, OnInit } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

// import service
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { ApiService } from '../../../services/api.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-featured-challenges',
  templateUrl: './featured-challenges.component.html',
  styleUrls: ['./featured-challenges.component.scss']
})
export class FeaturedChallengesComponent implements OnInit {

  /**
   * Show section flag
   */
  show_featured_challenges = false;


  /**
   * Featured Challenges
   */
  featured_callenges: any = [];


  /**
   * Constructor.
   * @param endpointsService  EndpointService Injection.
   * @param route  ActivatedRoute Injection.
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   * @param authService  AuthService Injection.
   */
  constructor(private apiService: ApiService,
              private authService: AuthService,
              private globalService: GlobalService,
              private router: Router,
              private route: ActivatedRoute,
              private endpointsService: EndpointsService,
              private logger: NGXLogger) { }

  /**
   * Component on initialized
   */
  ngOnInit() {
    this.fetchCurrentChallenges();
  }

  /**
   * Fetching present challenges
   */
  fetchCurrentChallenges() {
    const API_PATH = this.endpointsService.allChallengesURL('present');
    const SELF = this;
    SELF.apiService.getUrl(API_PATH).subscribe(
      data => {
        const CHALLENGE_COUNT = data.count;
        if (CHALLENGE_COUNT === 0) {
            SELF.show_featured_challenges = false;
        } else {
          SELF.show_featured_challenges = true;
            SELF.featured_callenges = data.results.slice(0, 3);
            console.log(SELF.featured_callenges);
        }
      },
      err => {
        SELF.globalService.handleApiError(err);
      },
      () => this.logger.info('Present-Featured challenges fetched!')
    );
  }

  /**
   * Navigate to a challenge page
   * @param id  challenge id
   */
   navigateToChallenge(id) {
      this.router.navigate(['/challenge/' + id]);
   }


}
