import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { NGXLogger } from 'ngx-logger';

// import service
import { GlobalService } from '../../../services/global.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { ApiService } from '../../../services/api.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-featured-challenges',
  templateUrl: './featured-challenges.component.html',
  styleUrls: ['./featured-challenges.component.scss'],
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
   * @param router  Router Injection.
   * @param globalService  GlobalService Injection.
   * @param apiService  ApiService Injection.
   */
  constructor(
    private endpointsService: EndpointsService,
    private router: Router,
    private globalService: GlobalService,
    private apiService: ApiService,
    private logger: NGXLogger
  ) {}

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
      (data) => {
        const CHALLENGE_COUNT = data.count;
        if (CHALLENGE_COUNT === 0) {
          SELF.show_featured_challenges = false;
        } else {
          SELF.show_featured_challenges = true;
          SELF.featured_callenges = data.results.slice(0, 3);
        }
      },
      (err) => {
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
