import { Component, OnInit, Input } from '@angular/core';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-confirm',
  templateUrl: './confirm.component.html',
  styleUrls: ['./confirm.component.scss'],
})
export class ConfirmComponent implements OnInit {
  /**
   * Input parameters object
   */
  @Input() params: any;

  /**
   * Confirm Title
   */
  title = 'Are you sure ?';

  /**
   * Confirm content
   */
  content = '';

  /**
   * confirm accept button
   */
  confirm = 'Yes';

  /**
   * Confirm deny button
   */
  deny = 'Cancel';

  /**
   * Confirm callback
   */
  confirmCallback = () => {};

  /**
   * Deny callback
   */
  denyCallback = () => {};

  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(private globalService: GlobalService) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    if (this.params['title']) {
      this.title = this.params['title'];
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

  /**
   * Confirm callback.
   */
  confirmed() {
    this.globalService.hideConfirm();
    this.confirmCallback();
  }

  /**
   * Deny callback.
   */
  denied() {
    this.globalService.hideConfirm();
    this.denyCallback();
  }
}
