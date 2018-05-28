import { Injectable, Output, EventEmitter } from '@angular/core';

@Injectable()
export class GlobalService {
  scrolledState = false;
  @Output() change: EventEmitter<boolean> = new EventEmitter();

  constructor() { }
  scrolledStateChange(s) {
    this.scrolledState = s;
    this.change.emit(this.scrolledState);
  }
}
