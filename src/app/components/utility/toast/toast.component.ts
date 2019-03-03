import { Component, OnInit, OnDestroy, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';
import { GlobalService } from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-toast',
  templateUrl: './toast.component.html',
  styleUrls: ['./toast.component.scss']
})
export class ToastComponent implements OnInit, OnDestroy {

  /**
   * Type of toast
   */
  type: any = 'success';

  /**
   * Toast message
   */
  message: any = 'Success';

  /**
   * Global Service subscription public
   */
  globalServiceSubscription: any;

  /**
   * Constructor.
   * @param document  Window document Injection.
   * @param globalService  GlobalService Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document,
              private globalService: GlobalService) { }

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.globalServiceSubscription = this.globalService.toast.subscribe(temp => {
      this.type = temp.type || 'success';
      this.message = temp.message || 'Success';
      if (this.message.length >= 40) {
        console.warn('Toast message length should be < 65 and < 40 for mobile devices.');
      }
      this.show(temp.duration);
    });
  }

  /**
   * Display Toast.
   * @param duration  toast display duration in seconds.
   */
  show(duration) {
    const TOAST = this.document.getElementById('toast');
    const TOAST_MESSAGE = this.document.getElementById('toastmessage');
    TOAST_MESSAGE.innerHTML = this.message;
    TOAST.className = TOAST.className + ' show';
    setTimeout(() => {
      TOAST.className = TOAST.className.replace('show', '');
    }, duration * 1000);
  }

  /**
   * Component on destroyed.
   */
  ngOnDestroy() {
    if (this.globalServiceSubscription) {
      this.globalServiceSubscription.unsubscribe();
    }
  }
}
