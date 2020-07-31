import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { NGXLogger } from 'ngx-logger';

// import service
import { GlobalService } from '../../../services/global.service';
import { ChallengeService } from '../../../services/challenge.service';
import { ApiService } from '../../../services/api.service';
import { EndpointsService } from '../../../services/endpoints.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-challengeoverview',
  templateUrl: './challengeoverview.component.html',
  styleUrls: ['./challengeoverview.component.scss']
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
   * To call the API inside modal for editing the challenge description
   */
  apiCall: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param challengeService  ChallengeService Injection.
   */
  constructor(private challengeService: ChallengeService, @Inject(DOCUMENT) private document: Document,
              private globalService: GlobalService, private apiService: ApiService,
              private endpointsService: EndpointsService, private logger: NGXLogger) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.challengeService.currentChallenge.subscribe(
    challenge => {
      this.challenge = challenge;
    });
    this.challengeService.isChallengeHost.subscribe(status => {
      this.isChallengeHost = status;
    });
  }

  editChallengeOverview() {
    const SELF = this;

    SELF.apiCall = (params) => {
      const BODY = JSON.stringify(params);
      SELF.apiService.patchUrl(
        SELF.endpointsService.editChallengeDetailsURL(SELF.challenge.creator.id, SELF.challenge.id),
        BODY
      ).subscribe(
          data => {
            SELF.challenge.description = data.description;
            SELF.globalService.showToast('success', 'The description is successfully updated!', 5);
          },
          err => {
            SELF.globalService.handleApiError(err, true);
            SELF.globalService.showToast('error', err);
          },
          () => this.logger.info('EDIT-CHALLENGE-DESCRIPTION-FINISHED')
        );
    };

    const PARAMS = {
      title: 'Edit Challenge Description',
      label: 'description',
      isEditorRequired: true,
      editorContent: this.challenge.description,
      confirm: 'Submit',
      deny: 'Cancel',
      confirmCallback: SELF.apiCall
    };
    SELF.globalService.showModal(PARAMS);
  }
}
