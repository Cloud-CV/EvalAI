import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TermsAndConditionsModalComponent } from './terms-and-conditions-modal.component';
import { GlobalService } from '../../../../services/global.service';
import { FormsModule } from '@angular/forms';

describe('TermsAndConditionsModalComponent', () => {
  let component: TermsAndConditionsModalComponent;
  let fixture: ComponentFixture<TermsAndConditionsModalComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [TermsAndConditionsModalComponent],
      providers: [GlobalService],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TermsAndConditionsModalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
