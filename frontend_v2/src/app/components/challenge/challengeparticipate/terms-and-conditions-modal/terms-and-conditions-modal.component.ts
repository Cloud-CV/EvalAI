import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../../services/global.service';

@Component({
  selector: 'app-terms-and-conditions-modal',
  templateUrl: './terms-and-conditions-modal.component.html',
  styleUrls: ['./terms-and-conditions-modal.component.scss'],
})
export class TermsAndConditionsModalComponent implements OnInit {
  /**
   * Input parameters object
   */
  @Input() params: any;

  /**
   * Modal title
   */
  title = 'Are you sure ?';

  /**
   * Modal field label
   */
  label = '';

  /**
   * Modal body
   */
  content = '';

  /**
   * Modal accept button
   */
  confirm = 'Yes';

  /**
   * Modal deny button
   */
  deny = 'Cancel';

  /**
   * Is checked terms and conditions input
   */
  termsAndConditions: any;

  /**
   * Modal confirmed callback
   */
  confirmCallback = () => {};

  /**
   * Modal denied callback
   */
  denyCallback = () => {};

  constructor(private globalService: GlobalService) {}

  ngOnInit() {
    if (this.params) {
      if (this.params['title']) {
        this.title = this.params['title'];
      }
      if (this.params['label']) {
        this.label = this.params['label'];
      }
      if (this.params['content']) {
        this.content = this.params['content'];
      }
      if (this.params['confirm']) {
        this.confirm = this.params['confirm'];
      }
      if (this.params['deny']) {
        this.deny = this.params['deny'];
      }
      if (this.params['confirmCallback']) {
        this.confirmCallback = this.params['confirmCallback'];
      }
      if (this.params['denyCallback']) {
        this.denyCallback = this.params['denyCallback'];
      }
    }
  }

  confirmed() {
    this.globalService.hideTermsAndConditionsModal();
    this.confirmCallback();
  }

  denied() {
    this.globalService.hideTermsAndConditionsModal();
    this.denyCallback();
  }
}
