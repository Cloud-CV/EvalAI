import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { NGXLogger } from 'ngx-logger';

// import service
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeoverview',
  templateUrl: './challengeoverview.component.html',
  styleUrls: ['./challengeoverview.component.scss'],
})
export class ChallengeoverviewComponent implements OnInit {
  /**
   * Challenge object
   */
  challenge: any = null;

  /**
   * Is challenge host
   */
  isChallengeHost = false;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(
    private challengeService: ChallengeService,
    @Inject(DOCUMENT) private document: Document,
    private globalService: GlobalService,
    private endpointsService: EndpointsService,
    private logger: NGXLogger
  ) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe((challenge) => {
      this.challenge = challenge;
    });
    this.challengeService.isChallengeHost.subscribe((status) => {
      this.isChallengeHost = status;
    });
  }
}
