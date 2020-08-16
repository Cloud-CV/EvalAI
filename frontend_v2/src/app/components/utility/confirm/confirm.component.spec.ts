import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmComponent } from './confirm.component';
import { GlobalService } from '../../../services/global.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';

describe('ConfirmComponent', () => {
  let component: ConfirmComponent;
  let fixture: ComponentFixture<ConfirmComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ConfirmComponent],
      providers: [GlobalService],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmComponent);
    component = fixture.componentInstance;
    const PARAMS = {
      title: 'Would you like to remove yourself ?',
      content: 'Note: This action will remove you from the team.',
      confirm: 'Yes',
      deny: 'Cancel',
      confirmCallback: () => {},
    };
    component.params = PARAMS;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
